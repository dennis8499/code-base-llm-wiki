from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / '.agents/skills/codebase-wiki/scripts'


class FunctionalExplorationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'api.py').write_text('def main():\n    return "new capability"\n', encoding='utf-8')
        (self.root / 'wiki').mkdir()
        (self.root / 'wiki/index.md').write_text('Old knowledge only\n', encoding='utf-8')
        spec = importlib.util.spec_from_file_location('functional_inventory', SCRIPTS / 'functional_inventory.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.scan = self.module.scan(self.root)

    def report(self):
        return {
            'schema': 'codebase-functional-exploration/v1', 'snapshot_id': self.scan['snapshot_id'],
            'functions': [{'id': 'FUNC-CLI', 'outcome': 'Return the new capability',
                           'flow': 'CLI entry calls main and returns text', 'dependencies': [], 'paths': ['api.py']}],
            'coverage': [{'path': f['path'], 'sha256': f['sha256'], 'status': 'checked',
                          'function_ids': ['FUNC-CLI'], 'reason': 'Read current source'} for f in self.scan['included']],
            'entrypoints': [{'entrypoint_id': e['entrypoint_id'], 'status': 'checked',
                             'function_ids': ['FUNC-CLI'], 'reason': 'Traced main'} for e in self.scan['entrypoint_candidates']],
            'gaps': [],
        }

    def test_current_source_inventory_does_not_depend_on_wiki(self):
        self.assertIn('api.py', {f['path'] for f in self.scan['included']})
        self.assertNotIn('wiki/index.md', {f['path'] for f in self.scan['included']})
        self.assertTrue(self.module.validate_report(self.scan, self.report())['complete'])

    def test_omitted_file_or_entrypoint_is_rejected(self):
        report = self.report(); report['coverage'] = []
        with self.assertRaises(ValueError): self.module.validate_report(self.scan, report)
        report = self.report(); report['entrypoints'] = []
        if self.scan['entrypoint_candidates']:
            with self.assertRaises(ValueError): self.module.validate_report(self.scan, report)

    def test_stale_source_digest_and_unknown_function_are_rejected(self):
        for field, value in [('sha256', '0' * 64), ('function_ids', ['FUNC-IMAGINARY'])]:
            report = self.report(); report['coverage'][0][field] = value
            with self.assertRaises(ValueError): self.module.validate_report(self.scan, report)
        report = self.report(); report['snapshot_id'] = 'sha256:' + '0' * 64
        with self.assertRaises(ValueError): self.module.validate_report(self.scan, report)

    def test_partial_or_unreadable_scope_cannot_be_complete(self):
        report = self.report(); report['coverage'][0]['status'] = 'partial'
        self.assertFalse(self.module.validate_report(self.scan, report)['complete'])
        scan = copy.deepcopy(self.scan); scan['read_issues'].append({'path': 'missing.py', 'reason': 'unreadable'})
        self.assertFalse(self.module.validate_report(scan, self.report())['complete'])

    def test_cli_scans_without_writes_and_validation_detects_new_source(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'explore-functions.py'), 'scan', '--root', str(self.root)],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.scan['snapshot_id'], json.loads(result.stdout)['snapshot_id'])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        report = self.report()
        (self.root / 'worker.py').write_text('def work():\n    return 42\n', encoding='utf-8')
        with self.assertRaises(ValueError): self.module.validate_report(self.module.scan(self.root), report)

    def test_explicit_saved_report_can_be_excluded_without_hiding_source_changes(self):
        report_path = self.root / 'docs/exploration.json'
        exclusions = ('docs/exploration.json',)
        self.scan = self.module.scan(self.root, exclude_paths=exclusions)
        report_path.parent.mkdir()
        report_path.write_text(json.dumps(self.report()), encoding='utf-8')
        command = [sys.executable, '-B', str(SCRIPTS / 'explore-functions.py'), 'validate',
                   '--root', str(self.root), '--report', str(report_path), '--exclude-path', exclusions[0]]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stderr)
        (self.root / 'api.py').write_text('def main():\n    return "changed"\n', encoding='utf-8')
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(2, result.returncode)


if __name__ == '__main__': unittest.main()

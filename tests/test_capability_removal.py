from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
INSTALLER_PATH = SKILL_ROOT / "scripts" / "install-framework.py"

REMOVED_PATHS = {
    ".agents/skills/codebase-wiki/references/guide-workflow.md",
    ".agents/skills/codebase-wiki/assets/guide-template.md",
    ".github/prompts/save-guide.prompt.md",
    ".github/prompts/onboarding-guide.prompt.md",
    ".github/agents/wiki-archaeologist.agent.md",
    ".github/agents/wiki-ingest.agent.md",
    ".github/agents/wiki-keeper.agent.md",
    ".github/agents/wiki-lint.agent.md",
    ".github/agents/wiki-query.agent.md",
    ".codex/agents/wiki-archaeologist.toml",
    ".codex/agents/wiki-ingest.toml",
    ".codex/agents/wiki-keeper.toml",
    ".codex/agents/wiki-lint.toml",
    ".codex/agents/wiki-query.toml",
}

ACTIVE_PROMPTS = {
    "business-analysis-doc.prompt.md",
    "code-archaeology.prompt.md",
    "export-notebooklm.prompt.md",
    "ingest-batch.prompt.md",
    "ingest-module.prompt.md",
    "lint-wiki.prompt.md",
    "new-adr.prompt.md",
    "query-wiki.prompt.md",
    "save-synthesis.prompt.md",
    "system-analysis-doc.prompt.md",
    "system-design-doc.prompt.md",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CapabilityRemovalBehaviorTests(unittest.TestCase):
    def test_active_contract_and_platform_adapters_drop_removed_capabilities(self) -> None:
        manifest = json.loads((SKILL_ROOT / "capabilities.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["contract_version"], 5)
        self.assertEqual(len(manifest["intents"]), 11)
        self.assertEqual(len(manifest["intent_groups"]), 11)
        self.assertTrue({"guide", "delegation"}.isdisjoint(manifest["intents"]))
        self.assertTrue({"guide", "delegation"}.isdisjoint(manifest["intent_groups"]))
        self.assertTrue(
            {"guide", "delegation"}.isdisjoint(manifest["entrypoints"]["copilot"])
        )

        for relative in sorted(REMOVED_PATHS):
            with self.subTest(path=relative):
                self.assertFalse((REPO_ROOT / relative).exists())

        prompt_root = REPO_ROOT / ".github" / "prompts"
        mapped_prompts = {
            name
            for names in manifest["entrypoints"]["copilot"].values()
            for name in names
        }
        self.assertEqual(mapped_prompts, ACTIVE_PROMPTS)
        for path in sorted(prompt_root.glob("*.prompt.md")):
            with self.subTest(prompt=path.name):
                self.assertIn('agent: "agent"', path.read_text(encoding="utf-8"))

        codex_config = (REPO_ROOT / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertNotIn("[agents]", codex_config)

    def test_upgrade_marks_removed_managed_paths_obsolete_without_deletion(self) -> None:
        installer = load_module("capability_removal_installer", INSTALLER_PATH)
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            for surface in ("copilot", "codex"):
                target = temp_root / f"fresh-{surface}"
                target.mkdir()
                installer.apply_install(REPO_ROOT, target, surface, "install")
                installed_state = json.loads(
                    (
                        target
                        / ".agents"
                        / "skills"
                        / "codebase-wiki"
                        / "install-state.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(installed_state["contract_version"], 5)
                for relative in REMOVED_PATHS:
                    with self.subTest(surface=surface, fresh_path=relative):
                        self.assertFalse((target / relative).exists())

            target = temp_root / "upgrade"
            target.mkdir()
            installer.apply_install(REPO_ROOT, target, "codex", "install")
            state_path = target / ".agents/skills/codebase-wiki/install-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            retained: dict[str, bytes] = {}
            for index, relative in enumerate(sorted(REMOVED_PATHS), 1):
                content = f"locally retained obsolete file {index}\n".encode()
                retained[relative] = content
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                state["files"][relative] = {
                    "kind": "file",
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            local_guide = target / "wiki/guides/local-guide.md"
            local_guide.parent.mkdir(parents=True, exist_ok=True)
            local_guide.write_text("# User-authored legacy Guide\n", encoding="utf-8")
            state["files"]["wiki/guides/local-guide.md"] = {
                "kind": "file",
                "sha256": hashlib.sha256(local_guide.read_bytes()).hexdigest(),
            }
            state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            plan = installer.plan_install(REPO_ROOT, target, "codex", "upgrade")
            self.assertEqual(set(plan["obsolete_paths"]), REMOVED_PATHS)
            self.assertFalse(any(path.startswith("wiki/") for path in plan["obsolete_paths"]))
            result = installer.apply_install(REPO_ROOT, target, "codex", "upgrade")
            self.assertEqual(set(result["obsolete_paths"]), REMOVED_PATHS)
            for relative, content in retained.items():
                with self.subTest(obsolete_path=relative):
                    self.assertEqual((target / relative).read_bytes(), content)
            self.assertEqual(local_guide.read_text(encoding="utf-8"), "# User-authored legacy Guide\n")

    def test_legacy_guide_data_remains_parseable(self) -> None:
        guide_text = """---
title: Legacy Operations Guide
type: guide
sources: []
last_updated: 2026-09-04
tags: [guide, legacy]
status: active
---

# Legacy Operations Guide

Existing Guide content remains readable after creator removal.
"""
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            wiki = repo / "wiki"
            guide_path = wiki / "guides" / "legacy-guide.md"
            guide_path.parent.mkdir(parents=True)
            guide_path.write_text(guide_text, encoding="utf-8")

            frontmatter = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-B",
                    str(SKILL_ROOT / "scripts/validate-frontmatter.py"),
                    str(wiki),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(
                frontmatter.returncode,
                0,
                frontmatter.stdout + frontmatter.stderr,
            )

            rebuild = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-B",
                    str(SKILL_ROOT / "scripts/rebuild-index.py"),
                    str(wiki),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(rebuild.returncode, 0, rebuild.stdout + rebuild.stderr)
            index_text = (wiki / "index.md").read_text(encoding="utf-8")
            self.assertIn("## Guides", index_text)
            self.assertIn("[[legacy-guide]]", index_text)

            log_text = """---
title: Wiki Activity Log
type: log
sources: []
last_updated: 2026-09-04
tags: [log]
status: active
---

# Activity Log

<!-- codebase-wiki:log-contract-v1 -->

## [2026-09-04] guide | Legacy Guide retained

- Affected pages: [[legacy-guide]]
"""
            (wiki / "log.md").write_text(log_text, encoding="utf-8")
            validate_log = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-B",
                    str(SKILL_ROOT / "scripts/validate-log.py"),
                    str(wiki / "log.md"),
                    "--repo-root",
                    str(repo),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(
                validate_log.returncode,
                0,
                validate_log.stdout + validate_log.stderr,
            )

        exporter = load_module(
            "capability_removal_notebooklm_exporter",
            SKILL_ROOT / "scripts" / "notebooklm_exporter.py",
        )
        page = exporter.InputFile(
            path="wiki/guides/legacy-guide.md",
            text=guide_text,
            digest="0" * 64,
        )
        self.assertEqual(exporter.wiki_page_group(page), "project-guides")

    def test_active_docs_and_framework_knowledge_match_removed_surface(self) -> None:
        active_docs = (
            "README.md",
            "Codex.md",
            "AGENTS.md",
            "docs/README.md",
            "docs/architecture/README.md",
            "docs/validation/README.md",
            "docs/workflows/README.md",
            "samples/README.md",
            "wiki/overview.md",
            "wiki/guides/framework-introduction.md",
            "wiki/modules/platform-hooks-and-guards.md",
            "wiki/modules/platform-adapters-and-release.md",
        )
        forbidden = (
            "/save-guide",
            "/onboarding-guide",
            "references/guide-workflow.md",
            "assets/guide-template.md",
            ".github/agents/",
            ".codex/agents/",
            "explicit-delegation",
        )
        for relative in active_docs:
            text = (REPO_ROOT / relative).read_text(encoding="utf-8").lower()
            for token in forbidden:
                with self.subTest(path=relative, token=token):
                    self.assertNotIn(token.lower(), text)

        coverage = (REPO_ROOT / "wiki/synthesis/codebase-functional-coverage.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "| `.agents/skills/` | supporting-technical | [[notebooklm-ba-functional-export]], [[business-analysis-document]], [[system-analysis-document]], [[system-design-document]] |",
            coverage,
        )
        preflight = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-B",
                str(SKILL_ROOT / "scripts/export-notebooklm.py"),
                "--root",
                ".",
                "--preflight",
                "--format",
                "json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(preflight.returncode, 0, preflight.stderr)
        payload = json.loads(preflight.stdout)
        self.assertTrue(payload["ready_to_export"], payload["warnings"])
        self.assertEqual(payload["coverage"]["uncovered_count"], 0)

        knowledge_index = REPO_ROOT / "docs/knowledge/index.md"
        if knowledge_index.is_file():
            text = knowledge_index.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                if "://" not in target and not target.startswith("#"):
                    with self.subTest(knowledge_link=target):
                        self.assertTrue((knowledge_index.parent / target).resolve().is_file())

        log = (REPO_ROOT / "wiki/log.md").read_text(encoding="utf-8")
        self.assertEqual(
            log.count("## [2026-09-04] update | 移除 Guide 與 Delegation active capabilities"),
            1,
        )


if __name__ == "__main__":
    unittest.main()

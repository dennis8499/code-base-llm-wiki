from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).parents[2] / ".codebase-wiki" / "runtime"
sys.path.insert(0, str(RUNTIME_ROOT))


class ContractTests(unittest.TestCase):
    def test_capability_manifest_declares_both_surfaces(self) -> None:
        manifest = json.loads(
            (Path(__file__).parents[2] / ".agents" / "skills" / "codebase-wiki" / "capabilities.json")
            .read_text(encoding="utf-8")
        )

        self.assertEqual(manifest["contract_version"], 1)
        self.assertIn("copilot", manifest["surfaces"])
        self.assertIn("codex", manifest["surfaces"])
        self.assertIn("query", manifest["intents"])
        self.assertFalse(manifest["intents"]["query"]["writes_by_default"])

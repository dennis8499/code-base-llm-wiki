from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parents[1]


class ContractTests(unittest.TestCase):
    def test_capability_manifest_declares_installer_contract_v2(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "capabilities.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(manifest["contract_version"], 2)
        self.assertEqual(manifest["surfaces"], ["copilot", "codex"])
        self.assertIn("query", manifest["intents"])
        self.assertFalse(manifest["intents"]["query"]["writes_by_default"])
        self.assertEqual(set(manifest["cli"]), {"install", "upgrade"})
        self.assertIn("install-framework.py install", manifest["cli"]["install"])
        self.assertIn("install-framework.py upgrade", manifest["cli"]["upgrade"])


if __name__ == "__main__":
    unittest.main()

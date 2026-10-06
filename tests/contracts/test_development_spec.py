import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("development_spec", SCRIPTS / "validate-development-spec.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DevelopmentSpecTests(unittest.TestCase):
    def document(self, status="ready", questions="[]"):
        return f'''---
type: synthesis
notebooklm_role: exclude
spec_revision: 2
spec_status: {status}
blocking_questions: {questions}
---
# 登入規格
## 1. 目的與範圍
會員登入；不包含註冊。
## 2. 適用專案
auth
## 3. 功能行為與限制
憑證錯誤回傳 401。
## 4. 相依契約與確認決策
POST /login 接受 account/password，成功回傳 token。
## 5. 驗收情境
- SCN-001：Given 錯誤密碼；When 登入；Then 回傳 401。
'''

    def test_standalone_ready_document(self):
        self.assertEqual([], module.validate(self.document()))

    def test_unanswered_decision_cannot_be_ready(self):
        self.assertTrue(module.validate(self.document(questions='[Q-001]')))
        self.assertEqual([], module.validate(self.document("draft", "[Q-001]")))

    def test_ready_requires_actual_scenario_and_content(self):
        self.assertTrue(module.validate(self.document().replace("Given 錯誤密碼", "{待確認}")))
        self.assertTrue(module.validate(self.document().replace("auth\n", "\n")))

    def test_contract_objects_are_allowed_and_extra_primary_sections_are_rejected(self):
        document = self.document().replace("成功回傳 token。", '成功回傳 {"token": "value"}。')
        self.assertEqual([], module.validate(document))
        self.assertTrue(module.validate(document + "\n## 6. Extra appendix\nContent\n"))

    def test_target_section_is_generic_and_no_longer_group_repo_scoped(self):
        self.assertTrue(module.validate(self.document().replace("適用專案", "適用 Repo")))


if __name__ == "__main__":
    unittest.main()

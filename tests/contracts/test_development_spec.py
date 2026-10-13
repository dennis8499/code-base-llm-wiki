import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/codebase-wiki/scripts"
sys.path.insert(0, str(SCRIPTS))
import development_spec

spec = importlib.util.spec_from_file_location("development_spec_cli", SCRIPTS / "validate-development-spec.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DevelopmentSpecTests(unittest.TestCase):
    def document(self, status="ready", questions="[]"):
        text = f'''---
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
        return self.reviewed(text) if status == "ready" else text

    def reviewed(self, text):
        text = text.replace("self_contained_review: passed\n", "")
        import re
        text = re.sub(r"reviewed_spec_digest: .*\n", "", text)
        return text.replace("type: synthesis", "self_contained_review: passed\nreviewed_spec_digest: " +
                            development_spec.review_digest(text) + "\ntype: synthesis", 1)

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
        self.assertEqual([], module.validate(self.reviewed(document)))
        self.assertTrue(module.validate(document + "\n## 6. Extra appendix\nContent\n"))

    def test_target_section_is_generic_and_no_longer_group_repo_scoped(self):
        self.assertTrue(module.validate(self.document().replace("適用專案", "適用 Repo")))

    def test_previously_accepted_non_self_contained_specs_fail(self):
        for before, after in (("憑證錯誤回傳 401。", "詳見 [[missing-ba]]。"),
                              ("憑證錯誤回傳 401。", "詳見不存在的 BA／SD 文件。"),
                              ("POST /login 接受 account/password，成功回傳 token。", "API 欄位 TBD。"),
                              ("Given 錯誤密碼；When 登入；Then 回傳 401。", "Given; When; Then.")):
            with self.subTest(after=after):
                result = development_spec.inspect(self.reviewed(self.document().replace(before, after)))
                self.assertFalse(result["ok"])
                self.assertEqual("fail", result["structural_status"])

    def test_unresolved_contract_examples_and_format_only_scenarios_fail(self):
        contract = "POST /login 接受 account/password，成功回傳 token。"
        for replacement in ('API 回應欄位為 `TBD`。', '```json\n{"token": "待確認"}\n```'):
            with self.subTest(contract=replacement):
                result = development_spec.inspect(self.reviewed(self.document().replace(contract, replacement)))
                self.assertEqual("fail", result["structural_status"])
        for empty in ("** **", "_ _", "???", "<br>"):
            with self.subTest(given=empty):
                text = self.document().replace("Given 錯誤密碼", "Given " + empty)
                self.assertTrue(module.validate(self.reviewed(text)))
        duplicate = self.document() + "\n  - SCN-001: Given a; When b; Then c.\n"
        self.assertTrue(module.validate(self.reviewed(duplicate)))

    def test_semantic_review_is_separate_and_expires_after_changes(self):
        text = self.document()
        self.assertEqual("recorded", development_spec.inspect(text)["semantic_status"])
        result = development_spec.inspect(text.replace("spec_revision: 2", "spec_revision: 3"))
        self.assertFalse(result["ok"])
        self.assertEqual("pass", result["structural_status"])
        self.assertEqual("review_required", result["semantic_status"])
        self.assertFalse(module.validate(self.document("draft")))

    def test_portable_export_rejects_local_dependencies_and_duplicate_scenarios(self):
        text = self.document().replace("適用專案", "適用 Repo")
        sections = tuple(s.replace("適用專案", "適用 Repo") for s in development_spec.SECTIONS)
        for extra in ("\n[[missing-page]]", "\n[BA](../ba.md)", "\n[spec][sd]\n[sd]: file:///C:/sd.md", "\n[missing][]"):
            self.assertTrue(development_spec.structural_errors(text + extra, sections, portable=True))
        self.assertFalse(development_spec.structural_errors(text + "\n參考公開標準 [HTTP](https://example.org/http)。", sections, portable=True))
        self.assertFalse(development_spec.structural_errors(text + "\n公開補充 [HTTP][]\n[http]: https://example.org/http\n", sections, portable=True))
        self.assertTrue(module.validate(self.reviewed(self.document() + "\n- SCN-001: Given a; When b; Then c.\n")))

    def test_code_example_cannot_supply_missing_headings_or_scenario(self):
        text = self.document().replace("## 3. 功能行為與限制", "```md\n## 3. 功能行為與限制\n```")
        self.assertTrue(module.validate(self.reviewed(text)))


if __name__ == "__main__":
    unittest.main()

# 測試目錄

測試依責任分組；從 Repo 根目錄執行 `python -m unittest discover -s tests -v`
即可遞迴發現全部測試。

| 目錄 | 責任 |
| --- | --- |
| `contracts/` | 公開 contract、目錄形狀與 capability removal |
| `fixtures/code-audit/` | 靜態 Codebase 健檢的多入口、transaction／設定／邏輯缺陷、Git 歷史、技術風險、業務疑點與覆蓋缺口驗收材料 |
| `contracts/test_code_audit_validator.py` | persisted audit 報告結構、來源存在性、finding IDs、摘要／coverage 計數與隔離 Git history 驗收 |
| `installer/` | Copilot／Codex installer surface 與升級生命週期 |
| `notebooklm/` | NotebookLM exporter、schema 與 acceptance runner |
| `release/` | release builder 與資產契約 |
| `samples/` | `samples/task-tracker` 的安裝與 E2E contract |
| `tgrep/` | pinned Windows x64 tgrep wrapper、版本／digest 與唯讀邊界 |
| `wiki/` | Wiki lint、stale、log、hooks 與規格驗證 |

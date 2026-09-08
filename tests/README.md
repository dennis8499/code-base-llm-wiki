# 測試目錄

測試依責任分組；從 Repo 根目錄執行 `python -m unittest discover -s tests -v`
即可遞迴發現全部測試。

| 目錄 | 責任 |
| --- | --- |
| `contracts/` | 公開 contract、目錄形狀與 capability removal |
| `installer/` | Copilot／Codex installer surface 與升級生命週期 |
| `notebooklm/` | NotebookLM exporter、schema 與 acceptance runner |
| `release/` | release builder 與資產契約 |
| `samples/` | `samples/task-tracker` 的安裝與 E2E contract |
| `wiki/` | Wiki lint、stale、log、hooks 與規格驗證 |

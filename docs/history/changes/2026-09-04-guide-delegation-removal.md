# 2026-09-04：移除 Guide／Delegation active capabilities

這是 Codebase LLM Wiki 產品變更摘要；原始 AI SDLC work records 已移除，不再作為
本 Repo 的工作流或知識層。

## 變更

- 從 capability contract 與雙平台入口移除 Durable Guide 建立能力與 Explicit Delegation。
- 保留既有 `type: guide` Wiki 頁面、歷史 log、索引與 exporter 的讀取相容性。
- Installer fresh install 不再複製已移除的 active resources；upgrade 以
  `obsolete_paths` 回報舊受管檔案且不自動刪除使用者內容。
- Copilot／Codex adapter、文件、coverage ledger 與 regression tests 同步更新。

## 產品證據

- `README.md`
- `.agents/skills/codebase-wiki/capabilities.json`
- `.agents/skills/codebase-wiki/scripts/install-framework.py`
- `tests/contracts/test_capability_removal.py`
- `wiki/guides/`

---
name: lint-wiki
description: >
  對 Wiki 執行完整健康檢查——找出陳舊頁面、孤島頁面、斷裂連結、
  缺失頁面、frontmatter 錯誤，產出健康報告與修復建議。
agent: "wiki-lint"
argument-hint: "可選：補充只報告問題，或報告後協助修復"
---

對 `wiki/` 執行完整健康檢查。

依序完整載入 [Lint checklist](../../.agents/skills/codebase-wiki/references/lint-checklist.md)
與 [Follow-up actions](../../.agents/skills/codebase-wiki/references/follow-up-actions.md)，
再執行 `python .agents/skills/codebase-wiki/scripts/lint-wiki.py wiki/`。

保留 deterministic 結果，完成兩項 `agent_review_required` 語意檢查，並先回報
八類 findings。未經確認不得修復；確認後只做 findings 支持的 bounded repair，
同步 index，且只追加一筆 lint log。Raw sources 保持唯讀。

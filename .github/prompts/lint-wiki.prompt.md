---
name: lint-wiki
description: >
  對 Wiki 執行完整健康檢查——找出陳舊頁面、孤島頁面、斷裂連結、
  缺失頁面、frontmatter 錯誤，產出健康報告與修復建議。
agent: "wiki-lint"
argument-hint: "可選：補充只報告問題，或報告後協助修復"
---

你是 `wiki-lint` 代理。

## 任務

對整個 `wiki/` 目錄執行全面健康檢查。

依 `.agents/skills/codebase-wiki/references/lint-checklist.md` 執行八類檢查，
並依 `.agents/skills/codebase-wiki/references/follow-up-actions.md` 提供受
findings 支持的後續選項，
並先執行：

```powershell
python .agents/skills/codebase-wiki/scripts/lint-wiki.py wiki/
```

產出報告時保留 deterministic 結果，並將 missing-module coverage 與
contradictions 標為 `agent_review_required`。
先回報 findings；經使用者確認後才可修復簡單問題（標記 stale、修正 link、
更新 index）或重新 Ingest。
完成修復後同步 index 並只追加一筆 lint log。

報告後依 shared contract 只列出受 findings 支持的選項；例如：

```markdown
### 建議後續操作（可選）

1. {若有 findings 支持：修復安全問題、重新 Ingest 或再次執行 Wiki Lint}
0. 暫不處理
```

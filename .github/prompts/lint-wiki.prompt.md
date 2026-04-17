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

## 檢查項目

依照 `.github/skills/codebase-wiki/references/lint-checklist.md` 執行 8 項檢查：

1. **Stale Pages** — sources 路徑是否仍存在
2. **Orphan Pages** — 是否有頁面無 inbound link
3. **Broken Links** — `[[wikilink]]` 目標是否存在
4. **Missing Pages** — 重要模組是否遺漏
5. **Frontmatter Validation** — 欄位完整性
6. **Contradictions** — 多頁描述同一實體時是否一致
7. **Index Completeness** — index.md 與實際檔案是否同步
8. **Coverage Report** — wiki 覆蓋率統計

## 自動化工具

可搭配執行：

- `python .github/skills/codebase-wiki/scripts/check-stale.py wiki/`
- `python .github/skills/codebase-wiki/scripts/wiki-stats.py wiki/`

## 輸出

產出標準健康報告後，列出建議的修復動作。
經使用者確認後可自動修復簡單問題（標記 stale、修正 link、更新 index）。
完成後追加 `wiki/log.md` 條目。

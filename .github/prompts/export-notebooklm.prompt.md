---
name: export-notebooklm
description: >
  先以 Wiki-first 流程確認專案知識，再產生符合 NotebookLM Enterprise
  限制的本地 Markdown source pack 與增量 upload plan。
agent: "wiki-keeper"
argument-hint: "可選：匯出範圍；預設為整個目前專案"
---

## 任務

準備目前專案給 NotebookLM Enterprise 使用。預設範圍是整個專案，但來源
選擇必須以 Wiki 為主，raw source 只限 Wiki `frontmatter.sources` 或明確設定
的 evidence paths。

## 流程

1. 讀取 `wiki/index.md`，再讀取整個專案相關 Wiki 頁面；不要把
   `wiki/log.md` 當作 project evidence。
2. 執行 frontmatter、stale-source 與 Wiki lint 檢查，辨識 placeholder、stale、
   缺口、矛盾與缺失來源。
3. 若需要重新萃取，先列出 bounded Batch/Interactive Ingest 範圍、預計更新頁面、
   index/log 變更與 raw paths；等待使用者確認，未確認前不修改 Wiki 或輸出 pack。
   若 preflight clean，沿用使用者已提出的 export request，不需重新掃描 raw tree。
4. 對已確認的 Ingest 範圍依既有 workflow 更新 Wiki，完成 `wiki/index.md` 與
   append-only `wiki/log.md`，再執行：

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --output .notebooklm --format json
   ```

5. 報告 `.notebooklm/upload-plan.md` 的 `added`、`changed`、`deleted`、
   `unchanged`、skipped、warnings 與剩餘 source slots。

## 限制與安全

- 不呼叫 NotebookLM API、不自動上傳、不修改 raw sources。
- 只上傳 `.notebooklm/sources/*.md`；不要上傳 manifest、upload plan 或 README。
- changed 的本地 static source 必須在 NotebookLM 移除舊檔後重新上傳；unchanged 不需重傳。
- 遇到超過 source count、單檔 byte/word limit 或敏感檔案時，保留舊 pack 並清楚報告，
  不得靜默截斷或略過未說明的內容。

---
name: export-notebooklm
description: >
  全量掃描安全的專案程式、設定、資料結構與既有文件，先預覽功能導向
  Ingest，再產生符合 NotebookLM Enterprise 限制的繁中 source pack。
agent: "wiki-keeper"
argument-hint: "可選：匯出範圍；預設為整個目前專案"
---

## 任務

準備目前專案給 NotebookLM Enterprise 使用。預設範圍是整個專案。既有 Wiki
是知識基線，不得作為 raw discovery 邊界；每次都必須重新建立完整安全範圍清單，
但只增量更新真正改變或缺漏的 Wiki 知識。

完整載入 `.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md`，
並以該 reference 作為 preflight、確認、文件優先與 pack completion criterion 的唯一來源。

## 流程

1. 讀取 `wiki/index.md` 與全部 Wiki Markdown（`wiki/log.md` 只作歷史，不作
   project evidence），並執行 frontmatter、stale-source 與 Wiki lint checks。
2. 執行唯讀 preflight：

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --preflight --format json
   ```

3. 讀取 preflight 納入的每個 UTF-8 檔案：runtime code、必要設定/manifests、
   schema/migrations 與既有文件。排除 tests、CI/CD、IaC、build/dev tooling、
   dependencies/generated、binary、credentials、framework adapters、Wiki 與 output。
4. 從 entrypoints、use cases、資料邊界、public interfaces 與 integrations 建立
   功能域，不要只照目錄切頁。回報掃描數量與排除原因、功能 coverage、預計新增/
   更新/不變的 Wiki pages、evidence、容量估計與 gaps，然後等待使用者確認。
   即使 Wiki clean 也必須預覽並確認；確認前不修改 Wiki 或產生 pack。
5. 確認後保留人工內容並增量建立：overview、project function catalog、system
   architecture、每個功能域的 module/entity pages、system analysis。敘述固定繁體
   中文，code identifiers 不翻譯；頁面使用穩定 kebab-case `notebooklm_group`，
   coverage 標成 covered/partial/gap。同步 index 並只追加一筆 `ingest` log。
6. 驗證 Wiki 後執行：

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --apply --preflight-id <id> --output .notebooklm --format json
   ```

7. 報告 `.notebooklm/upload-plan.md` 的 `added`、`changed`、`deleted`、
   `unchanged`、skipped、`source_budget` omissions、warnings 與剩餘 slots。

## 限制與安全

- 不呼叫 NotebookLM API、不自動上傳、不修改 raw sources。
- 只上傳 `.notebooklm/sources/*.md`；不要上傳 manifest、upload plan 或 README。
- changed 的本地 static source 必須在 NotebookLM 移除舊檔後重新上傳；unchanged 不需重傳。
- 文件永遠優先於 evidence；低優先 evidence 若無法容納，必須以 `source_budget`
  明列。必要文件或單檔無法符合 300 sources、200 MB / 500,000 words hard limits
  時保留舊 pack 並失敗，不得靜默截斷。

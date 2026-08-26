---
name: export-notebooklm
description: >
  全量掃描安全的業務文件與專案實作，先預覽 BA 流程／規則導向
  Ingest，再產生符合 NotebookLM Enterprise 限制的繁中業務知識 source pack。
agent: "wiki-keeper"
argument-hint: "可選：匯出範圍；預設為整個目前專案"
---

## 任務

準備目前專案給 NotebookLM Enterprise 使用。預設範圍是 `--root` 指定的整個專案目錄及其
全部子目錄。既有 Wiki 是知識基線，不得作為 raw discovery 邊界；每次都必須重新
建立完整安全範圍清單，但只增量更新真正改變或缺漏的 Wiki 知識。掃描以檔案系統
root 為準，不要求 root 有 `.git`、working tree clean，也不因 nested repository
阻擋；nested repository 的 `.git` metadata 仍依 generated 排除規則忽略。
使用 exporter 的 top-down exclusion-aware walker：保留 ignored、untracked 與 nested
repository 的 runtime source，但在進入排除目錄前剪枝。回報 file-level exclusions
與 directory-level excluded-root summaries；summary 只做 bounded metadata-only
觀察，不讀取或 hash 排除內容，`truncated` 或 metadata errors 必須保留為 warning。

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

3. 先讀 `business_source_paths` 指定的需求、流程、決策表或 acceptance spec，再讀
   preflight 納入的其他 UTF-8 runtime code、必要設定/manifests、schema/migrations
   與既有文件。未明確指定者仍排除 tests、CI/CD、IaC、build/dev tooling、
   dependencies/generated、binary、credentials、framework adapters、Wiki 與 output。
4. 依角色、觸發、前置條件、主／例外流程、業務結果、規則與狀態轉換建立業務能力，
   不要只照目錄切頁，也不要把實作行為當成正式政策。回報 included file counts、
   file-level exclusion reasons、pruned excluded-root counts/summaries、業務流程／規則／詞彙
   coverage、預計新增/更新/不變的 Wiki
   pages、evidence、容量估計、DLP status 與 gaps，然後等待使用者確認。
   即使 Wiki clean 也必須預覽並確認；確認前不修改 Wiki 或產生 pack。
5. 確認後保留人工內容並增量建立：BA overview、business process/rule catalogs、
   glossary、knowledge gaps，以及每個 process/rule page。BA pages 的
   `notebooklm_group` 使用穩定 `business-{capability}` 值，並設為
   `notebooklm_role: business`；選定工程頁只標成
   `traceability`。每項知識標示 business-confirmed、implementation-observed、
   inference 或 gap。同步 index 並只追加一筆 `ingest` log。
6. 驗證 Wiki 後重新執行 `--preflight`，取得文件更新後的 readiness ID；不得沿用
   discovery preflight ID。展示 readiness gates、容量、DLP、migration 與 gaps，等待
   第二次確認後再執行：

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --apply --preflight-id <id> --output .notebooklm --format json
   ```

7. 確認 exporter 產生 `sources/query-index.md` 與 `sources/project-map.md`；
   `query-index.md` 必須把 BA 問題類型、業務能力群組、process/rule/glossary pages、
   business evidence 與 technical traceability source IDs 對應起來。
8. 報告 `.notebooklm/upload-plan.md` 的 `added`、`changed`、`deleted`、
   `unchanged`、skipped、traceability `source_budget` omissions、DLP status、
   migration/full-rebuild status、warnings 與剩餘 slots，
   並說明 README 中的 Custom instructions 與同一本 Notebook 清空重傳步驟。

## 限制與安全

- 不呼叫 NotebookLM API、不自動上傳、不修改 raw sources。
- Exporter 會在本機執行 `notebooklm-enterprise-basic` DLP 檢核；未 allowlist 的
  finding 會阻擋 apply，報告不包含命中值。
- 只上傳 `.notebooklm/sources/*.md`；不要上傳 manifest、upload plan 或 README。
- NotebookLM 問答以 `query-index.md` 路由到最多五個業務能力群組；先以業務語言回答，
  正式政策查 business evidence，目前實作才查 traceability。未要求時不要以 path/API
  主導答案，也不得把 implementation-observed 說成核准政策。
- changed 的本地 static source 必須在 NotebookLM 移除舊檔後重新上傳；unchanged 不需重傳。
- BA 文件與指定 business evidence 永遠優先；低優先 technical traceability 若無法容納，
  必須以 `source_budget` 明列。必要 BA 內容或單檔無法符合 300 sources、200 MB /
  500,000 words hard limits
  時保留舊 pack 並失敗，不得靜默截斷。

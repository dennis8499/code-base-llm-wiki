---
name: export-notebooklm
description: >
  全量掃描安全 Codebase，一次確認後建立每個功能的現況 BA／SA，並產生符合
  NotebookLM Enterprise 限制與治理基準的單一 Notebook 本機文件包。
agent: "agent"
argument-hint: "可選：匯出範圍；預設為整個目前專案"
---

## 任務

準備目前專案給 NotebookLM Enterprise 使用。預設範圍是 `--root` 指定的整個專案目錄及其
全部子目錄。既有 Wiki 是知識基線，`docs/knowledge/` 是 canonical knowledge layer，
兩者均不得作為 raw discovery 邊界；每次都必須重新建立完整安全範圍清單，並全量重建
managed BA／SA sections、保留 user notes。當下
Codebase 是唯一內容依據，包含 README、規格、測試與註解；衝突時以程式碼為主，沒有
證據時寫 `Codebase 未提供證據`。掃描以檔案系統
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
   preflight 納入的其他 UTF-8 runtime code、必要設定/manifests、schema/migrations、
   behavioral tests 與既有文件。排除 CI/CD、IaC、build/dev tooling、
   dependencies/generated、binary、credentials、framework adapters、Wiki 與 output。
4. 依可觀察行為建立 stable `fr-*`／`cap-*` 與 `AC-*`，再連結角色、觸發、前置條件、
   主／例外流程、業務結果、規則與狀態轉換，
   不要只照目錄切頁，也不要把實作行為當成正式政策。回報 included file counts、
   file-level exclusion reasons、pruned excluded-root counts/summaries、業務流程／規則／詞彙
   requirement/process/rule coverage、每個 safe file disposition、預計重建的 Wiki
   pages、容量估計、DLP masking status 與 gaps，然後等待使用者確認。
   即使 Wiki clean 也必須預覽並確認；這是正常流程的一次確認，確認前不修改 Wiki 或產生 pack。
5. 確認後保留 user-notes 並全量重建 managed sections：BA overview、functional
   requirement/process/rule catalogs、glossary、knowledge gaps、coverage ledger，以及每個
   requirement/process/rule page。BA pages 的
   `notebooklm_group` 使用穩定 `business-{capability}` 值，並設為
   `notebooklm_role: business`；工程／coverage 頁標成 `exclude`。技術 provenance 放
   `notebooklm:local-only` markers。每個 active `cap-*` 另建立相同 group、互相連結且有
   `source_locators` 的 `{cap}-ba.md`（`codebase-business-analysis-v1`）與 `{cap}-sa.md`
   （`codebase-system-analysis-v1`）。每項知識標示 business-confirmed、
   implementation-observed、inference 或 gap。同步 index 並只追加一筆
   合法 log operation；framework maintenance 使用 `update`。
6. 完整處理後在 coverage ledger 記錄 confirmed discovery ID。驗證 Wiki 後重新執行
   `--preflight`，自動取得文件更新後的 readiness ID；這不新增人工 gate。若 raw/config/scope
   漂移則重新預覽並確認；若只有 Wiki 重建，沿用 discovery ID。接著直接執行：

   ```powershell
   python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
     --root . --apply --discovery-id <confirmed-id> `
     --preflight-id <latest-id> --output .notebooklm --format json
   ```

7. 確認 exporter 產生完整 `documents/{cap}-ba.md`／`-sa.md`、
   `sources/query-index.md`、`sources/project-map.md` 與 document/source mapping；
   `query-index.md` 必須同時路由 BA 與 SA 問題。
8. 報告 `.notebooklm/upload-plan.md` 的 `added`、`changed`、`deleted`、
   `unchanged`、skipped、coverage、DLP masking counts、
   migration/full-rebuild status、warnings 與剩餘 slots，
   並說明 README 中的 Custom instructions 與同一本 Notebook 清空重傳步驟。

## 限制與安全

- 不呼叫 NotebookLM API、不自動上傳、不修改 raw sources。
- Exporter 會在本機執行 `notebooklm-enterprise-ba-sa-mask-v1` DLP；analysis、documents 與
  sources finding 先遮罩，final residual 才阻擋 apply，報告不包含命中值且沒有 allowlist。
- 只上傳 `.notebooklm/sources/*.md`；documents、manifest、upload plan、governance 與 README 留在本機。
- NotebookLM 問答以 `query-index.md` 路由到最多五個業務能力群組；先以 `fr-*`、`AC-*`
  與業務語言回答，不得列 raw code、config、path/API 或 traceability，也不得把
  implementation-observed 說成核准政策。
- changed 的本地 static source 必須在 NotebookLM 移除舊檔後重新上傳；unchanged 不需重傳。
- 每個功能的 BA／SA 都必須映射到 source pack。完整內容或單檔無法符合 300 sources、500 MB /
  500,000 words hard limits
  時保留舊 pack 並失敗，不得靜默截斷。
- `governance.md` 依 Google 官方基準區分本機檢查與租戶管理員待驗證的 IAM、VPC Service
  Controls、CMEK、data location、Sensitive Data Protection 與 Model Armor，不宣稱雲端已生效。

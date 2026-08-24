---
title: NotebookLM Enterprise — 全專案功能文件化與離線匯出
type: guide
summary: 先完成功能文件與安全 preflight，再以相符 ID 原子產生增量 NotebookLM source pack
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - docs/workflows/README.md
source_digest: sha256:6ed3cab3860543d53aa182848346625eaa4e596ee8a697170abbcc831e528a62
derived_from: ["[[overview]]", "[[notebooklm-exporter]]", "[[project-function-catalog]]"]
last_updated: 2026-08-24
tags: [guide, notebooklm, export, incremental, enterprise]
status: active
notebooklm_group: project-guides
---

# NotebookLM Enterprise — 全專案功能文件化與離線匯出

> 每次安全掃描整個專案，依功能建立可搜尋的繁體中文 Wiki，再整理成可審查、
> 可手動上傳且可重跑比對的 NotebookLM source pack。這是離線產出流程，不是
> NotebookLM API 或自動同步服務。

## 適用情境

當維護者希望直接在單一 NotebookLM notebook 搜尋專案功能、架構、流程、資料模型、
設定、例外與風險時，使用 `/export-notebooklm` 或 Codex 的自然語言 recipe。既有
Wiki 是可複用的知識基線，但每次執行仍會重掃安全的全專案範圍，避免新增、刪除或
未覆蓋功能被既有 `frontmatter.sources` 遺漏。

## 執行前檢查

1. 執行 `--preflight`，列出 Git tracked 與 non-ignored untracked files 的分類結果。
2. 納入可分享的 runtime source、必要 config/manifests、schema/migrations 與既有文件。
3. 排除 tests、CI/CD、IaC、build/dev tooling、dependencies、generated/build/cache、binary、secrets、Wiki/output 與明確設定的 exclusions；預設 `target` profile 另排除 framework adapters。
4. 讀取全部 included files，依專案功能建立 source-to-function coverage map；讀 Wiki index/pages 判斷已覆蓋、stale、placeholder、矛盾與缺失文件。
5. 預覽 included/excluded inventory、功能群組、預計新增或重大更新頁面、來源數/容量估計、warnings 與未驗證事項；即使沒有問題也等待確認。
6. 人工確認預覽沒有不應分享的商業機密、個資、憑證或租戶政策衝突。

唯讀預覽命令：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --preflight --format json
```

Preflight 不建立或修改 `wiki/`、`.notebooklm/`。它回傳 `preflight_id`、
`inventory_hash`、必要文件與 lint 狀態；只有 `ready_to_export=true` 才可 apply。
功能語意、文件規劃與 coverage 判斷仍由 Agent 根據 included files 完成。

若前置 Query 或 Lint 已提出 follow-up action，NotebookLM export 仍須依本流程
單獨完成全專案 preflight 與使用者確認；Query/Lint 的文字選項不會自動觸發匯出。

## 確認後的文件化

Agent 以固定繁體中文敘事更新 Wiki，事實必須可由真實 repo-relative source paths
支持，推論、speculation 與 coverage gap 必須分開標示。最低文件集合為：

- `wiki/overview.md`：專案目的、範圍、主要入口與功能地圖；
- `wiki/synthesis/project-function-catalog.md`：功能清單、所屬群組、source coverage 與關聯頁；
- `wiki/architecture/system-architecture.md`：元件、依賴、資料與控制流程；
- 各功能的 module/entity pages：介面、主要流程、分支、資料、設定與錯誤行為；
- `wiki/synthesis/system-analysis.md`：跨功能分析、部署/NFR 證據、風險與 gaps。

每個 NotebookLM 文件頁使用穩定的 `notebooklm_group`，以 `sources` 保存 raw
evidence、`derived_from` 保存 Wiki 關係，並對非空 sources 寫入 `source_digest`。
頁面新增、刪除、改名或重大更新時同步
`wiki/index.md`；整個 composite workflow 在 `wiki/log.md` 尾端只追加一筆
`ingest` operation。再次匯出仍全量重掃，但只更新有證據變化的 Wiki 內容。

## 產生 source pack

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --apply --preflight-id <id> --output .notebooklm --format json
```

`--output` 必須是 repo root 下的 child directory；CLI override 會納入
`preflight_id`。更換輸出目錄、設定或任何輸入後，必須重新執行 preflight，不能沿用
舊 ID。

可把 `.agents/skills/codebase-wiki/assets/notebooklm.toml` 複製成 Repo root 的
`notebooklm.toml` 以調整 `source_limit`、`reserved_source_slots`、
`max_source_bytes`、`max_source_words`、`include_evidence`、`extra_paths` 或
`exclude_paths` 與 `scan_profile`。設定只能降低 hard limits，路徑必須是
Repo-relative；一般目標使用 `target`，本框架 Repo 使用 `framework`。若透過
`--config` 明確指定設定檔時，該檔案必須位於 Repo root 內、不是 symlink/reparse
path，且存在並是一般檔案；不存在或無法解析時 preflight/apply 會拒絕執行，不會靜默
套用預設值。

輸出目錄包含：

- `sources/*.md`：唯一應手動加入 NotebookLM 的 source files；
- `manifest.json`：schema v2、scan inventory/coverage、profile、設定 limits、input/output hashes、stable IDs、warnings、omitted evidence 與 skipped paths；
- `upload-plan.md`：本次相對上一次 manifest 的操作分類；
- `README.md`：給上傳者的本機操作摘要。

## 穩定識別與更新

每個 source 依 `notebooklm_group` 使用 stable `logical_source_id`，主要形式是
`docs:<group>` 與 `evidence:<group>`；需要合併或切分時使用 deterministic
compaction/part IDs。Schema v1 previous manifest 會在比較時轉成 v2 語意。重跑
exporter 後依 `upload-plan.md` 操作：

| 狀態 | NotebookLM 手動操作 |
| --- | --- |
| `added` | 上傳新 Markdown source |
| `changed` | 先移除舊 static source，再上傳新檔 |
| `deleted` | 移除 NotebookLM 中的舊 source |
| `unchanged` | 不需重新上傳 |

不要把 `manifest.json`、`upload-plan.md` 或 README 當成專案 evidence 上傳。
Exporter 會保留 output directory 中不由它管理的檔案；Git 預設忽略整個
`.notebooklm/`，並以 `.*.notebooklm-transaction.json` 與
`.*.notebooklm-transaction.lock` 忽略 output sibling recovery metadata；release builder
也不會把它打包。

## 容量與安全

Enterprise profile 的 hard limits 是每本 notebook 最多 300 sources、每個 source
最多 200 MB 與 500,000 words。Exporter 預設使用較低的 180 MB 與 450,000
estimated words safety limits，並可預留 source slots。打包順序固定為 documents-first：
完整功能文件先取得來源與容量預算，關鍵 evidence 再依功能優先序加入；不足時以
`source_budget` 透明省略低優先 evidence，而不是刪減必要文件。若文件本身超限或
無法安全切分，export 會在 atomic commit 前失敗並保留舊 pack。不同 Workspace tier
請在 `notebooklm.toml` 下調，不要把 Enterprise 設定當成所有租戶通用。
若 output replacement 在 commit 期間失敗，staging/backup rollback 也會保留上一份有效 pack；
transaction journal 與子程序終止 regression 已驗證下一次 apply 可恢復上一份有效 pack；
同一 output 的並行 commit 由 transaction lock 保護，已有 writer 時後來的程序會 fail closed；
但突然斷電、檔案系統 metadata durability 與各 host 的所有終止窗口仍需另行演練。
既有 `manifest.json` 與待寫入 pack file 的 path 都必須是 output directory 內的安全相對路徑；
若 manifest、輸出 key 被竄改或包含 path traversal，exporter 會拒絕套用並保留既有 pack。
既有 output tree 也不得含 symlink 或 Windows reparse point，避免複製或替換 pack 時
讀取 output 外部內容。output root 與通往它的既有 parent components 也不得是 symlink
或 reparse point；這項檢查在 path
canonicalization 前執行。
Wiki input tree 也會在讀取頁面前驗證為 regular tree；若 Wiki root 或其下層含 symlink
或 Windows reparse point，preflight 會先 fail closed，不會先讀取連結指向的外部頁面。
`--root` 本身若是 symlink 或 Windows reparse point，CLI 也會在 canonicalization 前
拒絕，避免命令列輸入繞過 repository boundary。

預設會回報並排除 secrets/credentials、binary、tests、CI/IaC、build/dev tooling、
generated/build/cache、platform fallback audit logs、dependency、framework adapter 目錄與 export output。任何
skipped、omitted、warning 或 unresolved item
都必須在交付報告中列出；人工審查仍負責確認商業機密、個資與租戶政策。

## 相關頁面與官方限制

- [[overview]] — 框架三層模型與離線 delivery pack 邊界
- [[framework-introduction]] — 安裝、Wiki-first 工作流與 deterministic checks
- [[release-and-update]] — release 排除本機 pack
- [[notebooklm-exporter]] — preflight identity 與 atomic apply 實作
- [[project-function-catalog]] — 本框架功能 coverage
- [[system-analysis]] — 必要 SA 與明確 gap
- Enterprise 上限與產品行為請以 [Google Cloud Gemini Notebook Enterprise 文件](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview?authuser=2) 為準；Workspace tier 的 source 限制可能不同，參考 [NotebookLM 說明](https://support.google.com/notebooklm/answer/16337734?hl=zh-Hant)。
- 靜態檔案、Google Drive 與同步行為請參考 [NotebookLM source types and sync](https://support.google.com/notebooklm/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en)；本框架選擇離線 static Markdown replacement。

## 未解決事項

- 本流程不包含 NotebookLM API、Drive 自動同步、權限配置或自動刪除 NotebookLM source；使用者仍需在企業版介面手動執行 upload plan。
- 實際可用 source 數量與 Workspace/Enterprise 租戶政策可能變動；執行前應確認管理員設定與官方文件。
- Preflight 的路徑分類是 deterministic heuristic；對單一專案特有的生成目錄、敏感資料或 runtime 邊界，仍需在確認階段人工校正或透過 `notebooklm.toml` 明確排除。

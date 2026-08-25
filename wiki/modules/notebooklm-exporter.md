---
title: NotebookLM 離線匯出器
type: module
summary: 以 Wiki-first query-index、必要文件閘門與原子輸出建立可直接定位問題的 NotebookLM source pack
notebooklm_group: function-notebooklm-export
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - tests/test_export_notebooklm.py
source_digest: sha256:bccd0a578db678179bb70f48318fa8205913b17c371067df4cf853c0005a7a41
derived_from: ["[[system-architecture]]", "[[wiki-quality-and-provenance]]"]
last_updated: 2026-08-25
tags: [module, notebooklm, exporter, preflight]
status: active
---

# NotebookLM 離線匯出器

## 職責

- 盤點 Git tracked 與 non-ignored untracked 的安全 UTF-8 專案證據。
- 在讀取任何 Wiki page 前先驗證 Wiki root 是 regular tree，拒絕 symlink/reparse point，
  避免安全檢查前讀取外部內容。
- CLI 也在 canonicalization 前拒絕 symlink/reparse root，避免 `--root` 入口繞過
  exporter 的 repository boundary。
- 直接 page collection API 同樣拒絕 symlink/reparse project root，不只依賴 CLI guard。
- 非 UTF-8 config、previous manifest 或 transaction journal 會轉成受控 `ExportError`，
  不讓 malformed state 穿透成 traceback。
- 以 Wiki、inventory、設定與 deterministic findings 建立穩定 `preflight_id`。
- 強制必要 overview、function catalog、architecture 與 SA 都為 active 且可匯出。
- 先配置文件 source slots，再依證據優先序加入 raw evidence。
- 產生 `query-index` direct-lookup router 與 `project-map` navigation source，將 Wiki-first
  Query 的路由、最多五個主要來源群組、文件優先與 evidence 查核契約帶入 NotebookLM。
- 以 `han_characters_plus_non_han_tokens` 加總模型估算 source words，避免混合繁中敘事與程式碼時低估容量。
- 排除 `.mypy_cache/`、`.ruff_cache/`、平台 fallback hook audit logs 等 generated state，不把本機 audit output 當成 evidence；
  sensitive filename/path components 也會被排除。
- 產生 schema-v3 manifest、upload plan、query index、project map 與 stable logical source IDs；
  manifest 暴露 `wiki-first-direct-lookup-v1` retrieval contract。
- 以 `notebooklm-enterprise-basic` 在本機檢查 `CREDIT_CARD_NUMBER`、
  `FINANCIAL_ACCOUNT_NUMBER`、`GCP_CREDENTIALS`、`GCP_API_KEY` 與 `PASSWORD`。
- 未 allowlist 的 DLP finding 會讓 preflight 不 ready，阻擋 apply 並保留既有 pack；
  報告只包含 path、line、rule、severity 與 fingerprint，不包含命中值。
- 套用既有 pack 前驗證 manifest source file 必須是 output 內的安全相對路徑；
  malformed 或 path-traversal manifest 會 fail closed 且保留既有 pack。
- commit 前驗證新輸出 keys 與既有 output tree；path traversal、正規化碰撞或 symlink/
  Windows reparse point
  會 fail closed。
- 明確指定的 `--config` 必須位於 Repo root 內、不是 symlink/reparse path，且存在並是
  可解析的 TOML 一般檔案；缺檔不會靜默回退到預設設定。
- `--output` 必須位於 repo root 之下，且 override 會納入 `preflight_id`；更換輸出目錄
  會使舊 ID 失效。
- output root 與其既有 parent components 不得透過 symlink 到達；檢查在 `resolve()` 前
  執行，避免 symlink output 繞過 atomic pack boundary。
- 敏感檔名／目錄判定使用 repo-relative path components，不會因 repository 的絕對父目錄
  名稱包含 `secrets` 或 `credentials` 而誤排除整個專案。
- Preflight 額外回報 `coverage.status`、未覆蓋路徑數量與明確 warning；`ready_to_export`
  只代表必要文件與 deterministic gate 通過，不代表全專案已被 Wiki sources 覆蓋。
- 在輸出限制或寫入失敗時保留上一份有效 pack。
- 以 sibling transaction lock 序列化同一 output 的 commit；並行 writer 會 fail closed，避免
  互相覆蓋 recovery journal。
- 若單一 UTF-8 字元或其他內容無法在 byte/word limits 內安全切分，會在 commit 前
  fail closed，不產生超限 source。

## 對外介面

```text
export-notebooklm.py --root . --preflight --format json
export-notebooklm.py --root . --apply --preflight-id sha256:... --output .notebooklm
```

直接 export、遺漏 ID、ID 與目前 inventory/config/Wiki/retrieval contract 不符，或
`ready_to_export=false` 時 apply 回傳 exit code 2 且不寫入。`scan_profile=target`
排除已安裝 framework adapter；本 Repo 使用 `framework`，把 framework schema、
雙平台 adapter 與 release tooling 視為產品證據。

設定可使用：

```toml
dlp_profile = "notebooklm-enterprise-basic"
dlp_allowlist = [
  { path = "docs/example.md", rule = "GCP_API_KEY", fingerprint = "sha256:<64 lowercase hex>" },
]
```

## Evidence

- `build_preflight()` 結合 lint、required-document status、inventory hashes 與 coverage summary。
- `build_preflight()` 與 `_preflight_identity()` 同時暴露並綁定
  `wiki-first-direct-lookup-v1` retrieval contract；preflight schema version 為 3。
- `collect_wiki_pages()` 在 page read 前驗證 Wiki regular tree；
  `tests/test_export_notebooklm.py::test_preflight_rejects_unsafe_wiki_tree_before_reading`
  以 invalid external junction 固定 fail-closed 邊界。
- `test_preflight_rejects_reparse_root_before_resolving` 固定 `--root` 的 CLI lexical
  boundary 不會被 `resolve()` 繞過。
- `test_invalid_utf8_config_is_rejected_without_traceback`、
  `test_invalid_utf8_previous_manifest_is_rejected_without_traceback` 與
  `test_invalid_utf8_transaction_journal_is_rejected_without_traceback` 固定 malformed
  state 的 structured failure。
- `main()` 在 apply 前重建 preflight 並比較 ID。
- `estimate_words()` 將 Han/CJK 字元與非 Han、非空白 token runs 分開加總；`limits.word_count_model` 將模型寫入 preflight 與 manifest。
- `scan_dlp_inputs()` 只掃描 export candidates 與 Wiki pages；`DlpFinding` 不保存敏感原文，
  `DLP_PROFILE` 與 allowlist 會納入 preflight identity。
- `test_dlp_basic_profile_reports_safe_findings_without_secret_values`、
  `test_dlp_block_preserves_previous_pack` 與
  `test_dlp_allowlist_requires_exact_fingerprint` 固定 DLP gate、safe report 與 pack rollback。
- `commit_output()` 使用 staging/backup 與 `os.replace()`；若 replacement 失敗，會回復既有 pack。
- `commit_output()` 寫入 active/committed transaction journal；下一次 apply 可在程序終止
  後復原舊 pack，再清理 stage/backup。
- 相容入口 `export-notebooklm.py` 只轉呼叫 canonical module，沒有第二套實作。
- `tests/test_export_notebooklm.py::test_preflight_and_apply_handle_500_wiki_pages` 以
  500 個 synthetic module 驗證大規模 Wiki 的 full preflight/apply 與 source-limit compaction。
- `query-index.md` 以 Wiki page metadata、headings、`frontmatter.sources` 與實際 evidence
  input 建立可追溯路由；README 提供 Custom instructions 與同一本 Notebook 的一次性清空重傳步驟。
- `tests/test_export_notebooklm.py::test_commit_output_restores_previous_pack_after_replacement_failure`
  以 replacement fault injection 驗證失敗時舊 manifest/source 保留且 staging/backup 清理。
- `tests/test_export_notebooklm.py::test_commit_output_recovers_after_process_kill` 以
  子程序在新 pack 可見後終止，驗證 journal recovery 恢復既有 manifest/source。
- `test_explicit_config_outside_repository_is_rejected_before_reading` 固定明確設定檔不會
  越過 Repo root 讀取。
- `test_commit_output_rejects_concurrent_writer` 驗證另一個程序持鎖時 commit 會 fail closed。
- transaction journal 與 lock filename 會被 inventory 分類為 generated；
  `test_output_transaction_journal_is_excluded_from_inventory` 防止 transaction state 變成 evidence；
  stage/backup/journal temporary artifact 也會被分類為 generated；root `.gitignore` 與
  release builder 同步排除整組 sibling recovery artifact。

## Contradictions

- v0.1 的 `--preflight` 是選填且必要文件只產生 warning；v0.2 改為不可繞過的寫入契約。

## Inferences

- Preflight ID 證明本機輸入集合未變，並不代表 NotebookLM 租戶政策或人工機密審查
  已完成。
- Query index 與 Custom instructions 只能約束來源選擇與回答格式，不能取代 NotebookLM
  私有的生成式 retrieval；若需要 deterministic 結果，仍應以本地 Wiki Query 為權威入口。

## Gaps

- 不呼叫 NotebookLM API，也不自動上傳、刪除或同步雲端 source。
- 本機 Basic profile 是 export-side approximation；租戶自訂 Advanced DLP／Model Armor
  template 仍可能在雲端額外檢核或阻擋。
- 租戶實際來源額度仍需由管理員確認。

## 相關頁面

- [[notebooklm-export]]
- [[project-function-catalog]]
- [[system-analysis]]

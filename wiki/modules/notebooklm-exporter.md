---
title: NotebookLM 離線匯出器
type: module
summary: 以強制 preflight identity、必要文件閘門與原子輸出建立可審查的增量 NotebookLM source pack
notebooklm_group: function-notebooklm-export
sources:
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - tests/test_export_notebooklm.py
source_digest: sha256:986d22ade8bf0be0909fe2a016ddfa989202ee42fd611964284a3e338f6318fe
derived_from: ["[[system-architecture]]", "[[wiki-quality-and-provenance]]"]
last_updated: 2026-08-24
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
- 排除 `.mypy_cache/`、`.ruff_cache/`、平台 fallback hook audit logs 等 generated state，不把本機 audit output 當成 evidence；
  sensitive filename/path components 也會被排除。
- 產生 schema-v2 manifest、upload plan、project map 與 stable logical source IDs。
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

直接 export、遺漏 ID、ID 與目前 inventory/config/Wiki 不符，或
`ready_to_export=false` 時皆回傳 exit code 2 且不寫入。`scan_profile=target`
排除已安裝 framework adapter；本 Repo 使用 `framework`，把 framework schema、
雙平台 adapter 與 release tooling 視為產品證據。

## Evidence

- `build_preflight()` 結合 lint、required-document status、inventory hashes 與 coverage summary。
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
- `commit_output()` 使用 staging/backup 與 `os.replace()`；若 replacement 失敗，會回復既有 pack。
- `commit_output()` 寫入 active/committed transaction journal；下一次 apply 可在程序終止
  後復原舊 pack，再清理 stage/backup。
- 相容入口 `export-notebooklm.py` 只轉呼叫 canonical module，沒有第二套實作。
- `tests/test_export_notebooklm.py::test_preflight_and_apply_handle_500_wiki_pages` 以
  500 個 synthetic module 驗證大規模 Wiki 的 full preflight/apply 與 source-limit compaction。
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

## Gaps

- 不呼叫 NotebookLM API，也不自動上傳、刪除或同步雲端 source。
- 租戶實際來源額度仍需由管理員確認。

## 相關頁面

- [[notebooklm-export]]
- [[project-function-catalog]]
- [[system-analysis]]

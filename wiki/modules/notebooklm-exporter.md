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
source_digest: sha256:9fea46c7e91827fdea7870b3956c246c342266697265c64775bf75e63e4c72d2
derived_from: ["[[system-architecture]]", "[[wiki-quality-and-provenance]]"]
last_updated: 2026-08-21
tags: [module, notebooklm, exporter, preflight]
status: active
---

# NotebookLM 離線匯出器

## 職責

- 盤點 Git tracked 與 non-ignored untracked 的安全 UTF-8 專案證據。
- 以 Wiki、inventory、設定與 deterministic findings 建立穩定 `preflight_id`。
- 強制必要 overview、function catalog、architecture 與 SA 都為 active 且可匯出。
- 先配置文件 source slots，再依證據優先序加入 raw evidence。
- 產生 schema-v2 manifest、upload plan、project map 與 stable logical source IDs。
- 在輸出限制或寫入失敗時保留上一份有效 pack。

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

- `build_preflight()` 結合 lint、required-document status 與 inventory hashes。
- `main()` 在 apply 前重建 preflight 並比較 ID。
- `commit_output()` 使用 staging/backup 與 `os.replace()`。
- 相容入口 `export-notebooklm.py` 只轉呼叫 canonical module，沒有第二套實作。

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

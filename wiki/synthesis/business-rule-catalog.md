---
title: 業務規則目錄
type: synthesis
summary: NotebookLM 現況 BA／SA 知識交付與一般 BA／SA／SD 文件產出的規則、適用流程、證據狀態與例外
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務規則, codebase-only, code wins, readiness preflight, 證據優先序, standard-aligned, Gap]
sources: []
derived_from: ["[[business-process-catalog]]", "[[notebooklm-ba-knowledge-export]]", "[[generate-analysis-document]]"]
last_updated: 2026-09-04
tags: [synthesis, business-rule-catalog, notebooklm]
status: active
---

# 業務規則目錄

<!-- codebase-wiki:managed:start -->

## 規則覆蓋矩陣

| 規則 ID | 規則 | 適用流程 | 證據狀態 | 待確認事項 |
| --- | --- | --- | --- | --- |
| `br-notebooklm-ba-knowledge-first` | [[ba-knowledge-precedes-traceability]] | [[notebooklm-ba-knowledge-export]] | business-confirmed | 無 |
| `br-notebooklm-readiness-preflight` | [[readiness-preflight-required]] | [[notebooklm-ba-knowledge-export]] | business-confirmed | 無 |
| `br-analysis-standard-aligned-not-conformance` | [[standards-alignment-not-conformance]] | [[generate-analysis-document]] | business-confirmed | formal conformance 需另行稽核 |
| `br-analysis-missing-evidence-gap` | [[missing-evidence-remains-gap]] | [[generate-analysis-document]] | business-confirmed | Gap 可存在但不可被推測取代 |

## 規則衝突與例外

- Raw evidence 永不直接進入 upload sources；每 capability 的 BA／SA 也不可靜默省略。
- DLP finding 必須在 analysis、documents 與 sources 遮罩，final payload 有殘留時阻擋；沒有 allowlist。
- 歷史 schema v1–v5 或舊 retrieval contract 不與 schema-v6 BA／SA sources 混合，必須 full rebuild。
- BA／SA／SD 的 standards profile 只組織文件與 coverage，不代表 ISO／IEEE／IIBA
  conformance；IEEE 1016-2009 只作 informative 歷史參考。
- 缺少 BA／SA 上游或 Mermaid evidence 時，文件仍產出，但必須保留具體 Gap。
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

## 相關頁面

- [[business-process-catalog]]
- [[functional-requirement-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]

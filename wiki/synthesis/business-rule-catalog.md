---
title: 業務規則目錄
type: synthesis
summary: NotebookLM BA 知識交付的規則、適用流程、證據狀態與例外
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務規則, BA-first, readiness preflight, 證據優先序]
sources: []
derived_from: ["[[business-process-catalog]]", "[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
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

## 規則衝突與例外

- Raw evidence 與 technical traceability 永不進入 BA source pack；BA 文件也不可靜默省略。
- DLP finding 必須遮罩，final payload 有殘留時阻擋；schema v5 沒有 allowlist。
- 歷史 schema v1–v4 pack 不與 `business-only-ba-v2` pack 增量混合，必須 full rebuild。
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

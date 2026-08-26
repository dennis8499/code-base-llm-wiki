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

## 規則覆蓋矩陣

| 規則 ID | 規則 | 適用流程 | 證據狀態 | 待確認事項 |
| --- | --- | --- | --- | --- |
| `br-notebooklm-ba-knowledge-first` | [[ba-knowledge-precedes-traceability]] | [[notebooklm-ba-knowledge-export]] | business-confirmed | 無 |
| `br-notebooklm-readiness-preflight` | [[readiness-preflight-required]] | [[notebooklm-ba-knowledge-export]] | business-confirmed | 無 |

## 規則衝突與例外

- 技術 traceability 可依預算省略，但 BA 文件與指定 business evidence 不可靜默省略。
- DLP allowlist 只能精確處理已知 false positive，不能關閉 sensitive path 與內容安全邊界。
- 歷史 schema v1–v3 pack 不與 BA-first pack 增量混合，必須 full rebuild。

## 相關頁面

- [[business-process-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]


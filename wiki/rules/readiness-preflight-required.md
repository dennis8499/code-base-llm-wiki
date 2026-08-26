---
title: Readiness preflight 與第二次確認是匯出前置條件
type: business-rule
summary: BA 文件更新後必須重跑 readiness preflight，並以第二次確認的最新 ID 才能產生 pack
rule_id: br-notebooklm-readiness-preflight
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: business-confirmed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [readiness preflight, preflight ID, 第二次確認, ready to export]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:5106684498c329561f25e419d8dd19e52a4d227c2ae958aee26dd06c42bafce8
derived_from: ["[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
tags: [business-rule, notebooklm, readiness]
status: active
---

# Readiness preflight 與第二次確認是匯出前置條件

<!-- codebase-wiki:managed:start -->

## 規則敘述

Discovery preflight 只用來確認 BA 文件計畫。任何 Wiki 更新都會使其 ID 失效；完成文件後
必須重新 preflight，展示 readiness gates、完整 disposition、exact pack plan、DLP masking、
migration 與 gaps，取得第二次確認，
再以該次 ID apply。

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| 只有 discovery ID | 禁止 apply | 無 | business-confirmed |
| 必備 requirement/process/rule、coverage ledger 或 lint 未通過 | `ready_to_export=false`，修正後重跑 | 無；uncovered 與 analysis-gap 都必須清零 | business-confirmed |
| Final payload DLP 遮罩後仍有 finding | 阻擋 commit 並保留舊 pack | 無 allowlist | business-confirmed |
| readiness 後 Wiki、inventory、設定或 output 改變 | 舊 ID 失效，重跑 preflight 與確認 | 無 | business-confirmed |
| readiness 成功且第二次確認完成 | 可原子產生 pack | 寫入失敗仍保留上一份有效 pack | business-confirmed |

## 適用流程

- [[notebooklm-ba-knowledge-export]]

## 資料與詞彙

- `discovery preflight`：唯讀盤點與 BA 文件計畫預覽。
- `readiness preflight`：文件完成後的結構、安全、容量與 identity 驗證。
- `preflight_id`：綁定當下 Wiki、safe inventory、設定與 retrieval contract 的一次性識別。

## 待確認事項

無。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[notebooklm-exporter]]（實作細節不內嵌於本 BA 規則頁）
<!-- notebooklm:local-only:end -->

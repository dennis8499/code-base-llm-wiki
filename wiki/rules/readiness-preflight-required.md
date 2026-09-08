---
title: Readiness preflight 與雙識別碼是匯出前置條件
type: business-rule
summary: 一次確認鎖定 raw discovery；文件更新後自動重跑 readiness，並以相符雙識別碼產生 pack
rule_id: br-notebooklm-readiness-preflight
applies_to: ["[[notebooklm-ba-knowledge-export]]"]
evidence_state: business-confirmed
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [discovery ID, readiness preflight, preflight ID, 一次確認, ready to export]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:35a31655241118279815e3d73fa1c86b9831de192a6975b7271248010b67b526
derived_from: ["[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-09-08
tags: [business-rule, notebooklm, readiness]
status: active
---

# Readiness preflight 與雙識別碼是匯出前置條件

<!-- codebase-wiki:managed:start -->

## 規則敘述

Discovery 預覽用來確認完整 raw source snapshot、capability 與 BA／SA 文件計畫，使用者只需
確認一次。文件更新完成後，系統自動重跑 readiness，檢查完整 disposition、BA／SA pair、
source locators、exact pack plan、DLP、容量、migration 與 gaps，再以原 confirmed
`discovery_id` 及最新 `preflight_id` apply。

## 條件與結果

| 條件 | 決策／結果 | 例外 | 證據狀態 |
| --- | --- | --- | --- |
| 只有 discovery ID 或只有 preflight ID | 禁止 apply | 無 | business-confirmed |
| BA／SA pair、coverage ledger、source locator 或 lint 未通過 | `ready_to_export=false`，修正後自動重跑 | 無；uncovered 與 analysis-gap 都必須清零 | business-confirmed |
| Final payload DLP 遮罩後仍有 finding | 阻擋 commit 並保留舊 pack | 無 allowlist | business-confirmed |
| confirmed discovery 後 raw inventory 或 discovery 設定改變 | discovery ID 失效，停止並重新預覽及確認 | 不得混用 snapshot | business-confirmed |
| 文件或 final source plan 改變 | 保留相符 discovery ID，舊 preflight ID 失效並自動重算 | 不增加人工確認 | business-confirmed |
| readiness 成功且雙 ID 相符 | 可原子產生 pack | 寫入失敗仍保留上一份有效 pack | business-confirmed |

## 適用流程

- [[notebooklm-ba-knowledge-export]]

## 資料與詞彙

- `discovery_id`：只綁定當下安全 raw inventory、discovery 設定與排除，不因 Wiki 或 canonical `docs/knowledge/` 文件化而改變。
- `readiness preflight`：文件完成後的配對、結構、安全、容量與 final plan 驗證。
- `preflight_id`：綁定 confirmed discovery、最新 Wiki 與 exact upload-source plan 的一次性識別。

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

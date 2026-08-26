---
title: 建立 NotebookLM BA 功能需求包
type: business-process
summary: 知識維護者經全量萃取與 readiness 檢核，把 BA-only 功能需求交付到單一 Notebook
process_id: bp-notebooklm-ba-knowledge-export
actors: [知識維護者, Business Analyst, 業務擁有者]
coverage_status: covered
notebooklm_group: business-notebooklm-export
notebooklm_role: business
notebooklm_terms: [NotebookLM 匯出, 全量萃取, readiness preflight, BA-only source pack, Business Analyst]
sources:
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
source_digest: sha256:5106684498c329561f25e419d8dd19e52a4d227c2ae958aee26dd06c42bafce8
derived_from: ["[[overview]]", "[[notebooklm-export]]"]
last_updated: 2026-08-26
tags: [business-process, notebooklm, export]
status: active
---

# 建立 NotebookLM BA 功能需求包

<!-- codebase-wiki:managed:start -->

## 業務目的與範圍

把完整安全 codebase 的可觀察行為整理成功能需求、驗收條件、流程、規則、詞彙與缺口，
形成 BA 可直接詢問的 NotebookLM source pack。Raw code、設定與技術追溯只作本機分析，
不進入上傳來源。流程止於本地 pack 與手動 upload plan，不包含雲端操作自動化。

## 角色

| 角色 | 責任 |
| --- | --- |
| 知識維護者 | 盤點證據、提出文件計畫、維護 Wiki、執行 preflight 與產生 pack |
| Business Analyst | 檢視流程、規則、詞彙與 gaps 是否足以回答業務問題 |
| 業務擁有者／PO | 確認政策性規則與證據不足事項；未確認前不得標成 business-confirmed |

## 觸發與前置條件

- 觸發：使用者明確要求建立或更新 NotebookLM BA source pack。
- 前置：存在可讀的 repo root、Codebase LLM Wiki schema 與安全 UTF-8 文字來源。
- 非文字來源尚未轉換時不阻止盤點，但必須登記 gap。

## 主流程

| 步驟 | 角色 | 業務行為 | 結果 | 證據狀態 |
| --- | --- | --- | --- | --- |
| 1 | 知識維護者 | 執行唯讀 discovery preflight，盤點安全來源、排除、既有 coverage、DLP 與容量 | 形成文件計畫，不寫 Wiki 或 pack | business-confirmed |
| 2 | BA／業務擁有者 | 審查流程、規則、詞彙與 gap 計畫 | 第一次確認或要求調整 | business-confirmed |
| 3 | 知識維護者 | 全量重新萃取 managed BA sections、保留 user notes、完成 file disposition | 形成可審查且完整的持久功能需求 | business-confirmed |
| 4 | 知識維護者 | 執行第二次 readiness preflight | 取得與最新 Wiki／inventory／設定綁定的新 ID | business-confirmed |
| 5 | BA／業務擁有者 | 審查 readiness gates、容量、DLP、migration 與 gaps | 第二次確認或退回修正 | business-confirmed |
| 6 | 知識維護者 | 以第二次 ID 原子產生 pack | 取得 BA-only sources、schema v5 manifest 與 upload plan | business-confirmed |
| 7 | 交付者 | 依 upload plan 在同一本 Notebook 更新 static sources | 完成功能需求導向的 BA 問答資料集 | business-confirmed |

## 替代與例外流程

- 若缺少必備 BA 文件、active requirement/process、catalog link、AC ID、完整 disposition 或合法 `applies_to`，readiness
  不通過；先修正 Wiki，再產生新 ID。
- 若 Wiki、inventory、設定或 retrieval contract 在 preflight 後改變，舊 ID 失效。
- DLP finding 先遮罩；若 exact final payload 仍有殘留、必要內容超過容量，或 output boundary 不安全，保留上一份 pack。
- 若上一份 manifest 是 schema v1–v4 或非 `business-only-ba-v2`，採 full rebuild，不混用舊來源。

## 業務規則

- [[ba-knowledge-precedes-traceability]]
- [[readiness-preflight-required]]

## 輸入、輸出與狀態轉換

| 階段 | 輸入 | 狀態 | 輸出 |
| --- | --- | --- | --- |
| Discovery | Wiki baseline、安全 inventory、設定 | `discovery_pending` → `plan_confirmed` | coverage 與 BA 文件計畫 |
| Knowledge update | 已確認計畫、來源證據 | `knowledge_updating` → `knowledge_ready` | BA Wiki、index、log |
| Readiness | 最新 Wiki/inventory/settings | `readiness_pending` → `ready_to_export` | 新 preflight ID |
| Delivery | 第二次確認與相符 ID | `ready_to_export` → `pack_generated` | schema-v5 local pack |

## 上下游影響

- 上游：業務文件、程式／設定觀察、領域擁有者確認與既有 Wiki。
- 下游：NotebookLM BA 問答、人工審查、後續 gap closure 與 incremental upload plan。

## 成功結果

BA 能以功能需求 ID 與驗收條件回答目的、角色、流程、規則、資料語意與 gaps，且上傳來源
不洩漏 raw code、設定或 repository path。交付者另以固定 BA 題組完成 tenant UAT。

## 待確認事項

- `gap-notebooklm-non-text-evidence`：未轉成 UTF-8 repo text 的業務證據由誰整理與核准？
- `gap-notebooklm-tenant-uat`：目標 NotebookLM tenant 的實際回答是否通過固定 BA 題組？

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯關聯

- [[notebooklm-exporter]]（只有需要實作定位時才進入此 traceability page）
- [[notebooklm-export]]（操作者命令與安全檢查另置於此 traceability guide）
<!-- notebooklm:local-only:end -->

## 相關頁面

- [[business-process-catalog]]
- [[functional-requirement-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]

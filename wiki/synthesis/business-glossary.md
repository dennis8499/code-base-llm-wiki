---
title: 業務詞彙表
type: synthesis
summary: NotebookLM BA 知識交付與 BA／SA／SD 文件中的名詞、別名、狀態語意與流程規則關聯
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務詞彙, 功能需求, 驗收條件, BA-only, codebase disposition, knowledge gap, standards profile, coverage status, solution-neutral, architecture view]
sources: []
derived_from: ["[[overview]]", "[[business-process-catalog]]", "[[business-rule-catalog]]", "[[business-analysis]]", "[[system-analysis]]", "[[system-design]]"]
last_updated: 2026-09-04
tags: [synthesis, business-glossary, notebooklm]
status: active
---

# 業務詞彙表

<!-- codebase-wiki:managed:start -->

| 詞彙 | 別名 | 業務定義 | 狀態／值語意 | 關聯流程／規則 | 證據狀態 |
| --- | --- | --- | --- | --- | --- |
| 功能需求 | functional requirement | 以 `fr-*` 描述角色在條件下需要的系統行為與可觀察結果 | 每頁至少一個 `AC-*` | [[notebooklm-ba-functional-export]] | implementation-observed |
| BA 主文件 | business documentation | 以功能需求、驗收條件、流程、規則、詞彙與 gaps 說明系統 | `notebooklm_role: business`，唯一可上傳知識類型 | [[notebooklm-ba-knowledge-export]] | business-confirmed |
| Analysis evidence | 分析證據 | Raw source、config、test、schema 或 business-owned text 的唯讀本機副本 | 可被 DLP 遮罩，但永不直接上傳 | [[ba-knowledge-precedes-traceability]] | implementation-observed |
| Codebase disposition | 檔案歸屬 | 每個安全檔案對功能需求的分類 | uncovered 與 `analysis-gap` 都阻擋匯出 | [[notebooklm-ba-functional-export]] | implementation-observed |
| Discovery preflight | 發現預檢 | 第一次唯讀盤點，用來確認 BA coverage 與文件計畫 | ID 不可在 Wiki 更新後 apply | [[readiness-preflight-required]] | business-confirmed |
| Readiness preflight | 就緒預檢 | BA 文件完成後的結構、安全、容量與 identity 驗證 | 成功且第二次確認後才可 apply | [[readiness-preflight-required]] | business-confirmed |
| Knowledge gap | 業務知識缺口 | 無可靠文字證據、互相矛盾或需要 stakeholder 確認的問題 | open／resolved；不得以臆測填補 | [[business-knowledge-gaps]] | business-confirmed |
| Full rebuild | 完整重建 | 移除同一本 Notebook 的舊 static sources，再上傳全部 schema v5 BA-only sources | schema v1–v4 或舊 retrieval contract migration 必須使用 | [[notebooklm-ba-knowledge-export]] | business-confirmed |
| Business Analysis document | BA文件 | 說明 business context、value、stakeholders、current/target、capability、process/rule、KPI 與 change impact 的 standalone Markdown | `business-analysis-aligned-v1`; optional NotebookLM business content | [[generate-analysis-document]] | implementation-observed |
| System Analysis document | SA文件 | 說明 system boundary、stakeholder needs、use cases、SR/NFR/IF、概念資訊流、failure 與 V&V needs 的 solution-neutral Markdown | `system-analysis-aligned-v1`; traceability only | [[generate-analysis-document]] | implementation-observed |
| System Design document | SD文件／SDD | 說明 stakeholders/concerns、viewpoints/views、decisions、components、runtime、data、deployment、security 與 quality strategy | `system-design-aligned-v1`; traceability only | [[generate-analysis-document]] | implementation-observed |
| Standards profile | 標準設定檔 | 鎖定 standards editions、layer boundary、章節、coverage、IDs 與 diagram rules 的 versioned contract | v1 edition 不會靜默更新 | [[standards-alignment-not-conformance]] | business-confirmed |
| Standard-aligned | 標準對齊 | 依 profile 組織內容並提供 mapping/coverage evidence | 不等於 conformance、認證或稽核 | [[standards-alignment-not-conformance]] | business-confirmed |
| Coverage status | 覆蓋狀態 | 文件的 evidence completeness | covered / partial / gap；與 `status: active` freshness 分離 | [[missing-evidence-remains-gap]] | business-confirmed |
| Solution-neutral | 解法中立 | 描述 externally observable need/requirement，不指定 technology、component allocation 或 deployment design | SA boundary；solution choices 移至 SD/ADR | [[system-analysis-document]] | business-confirmed |
| Architecture view | 架構視圖 | 依 viewpoint 回應特定 stakeholder concerns 的 model | stable `VIEW-{SCOPE}-{SLUG}`，與其他 views/DE/ADR 建立 correspondence | [[system-design-document]] | implementation-observed |
| Design element | 設計元素／決策項 | 將 SA driver 映射到 selected approach、views 與 verification strategy 的 stable identity | `DE-{SCOPE}-NNN`; observed 不等於 approved ADR | [[system-design-document]] | implementation-observed |

## 詞彙衝突

- `evidence` 是本機分析輸入，不是 NotebookLM upload source；schema v5 不再匯出
  `business evidence` 或 `technical traceability` raw text。
- `ready_to_export` 代表 deterministic readiness gates 通過，不代表所有業務問題已有答案；
  已登記 gaps 可以存在。

## 待確認事項

- NotebookLM tenant UI 對 Custom instructions 的實際名稱與可用性可能依版本／政策不同。
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

---
title: 業務詞彙表
type: synthesis
summary: NotebookLM BA 知識交付中的名詞、別名、狀態語意與流程規則關聯
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務詞彙, 功能需求, 驗收條件, BA-only, codebase disposition, knowledge gap]
sources: []
derived_from: ["[[overview]]", "[[business-process-catalog]]", "[[business-rule-catalog]]"]
last_updated: 2026-08-26
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

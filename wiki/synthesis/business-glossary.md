---
title: 業務詞彙表
type: synthesis
summary: NotebookLM BA 知識交付中的名詞、別名、狀態語意與流程規則關聯
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務詞彙, BA 主文件, business evidence, technical traceability, knowledge gap]
sources: []
derived_from: ["[[overview]]", "[[business-process-catalog]]", "[[business-rule-catalog]]"]
last_updated: 2026-08-26
tags: [synthesis, business-glossary, notebooklm]
status: active
---

# 業務詞彙表

| 詞彙 | 別名 | 業務定義 | 狀態／值語意 | 關聯流程／規則 | 證據狀態 |
| --- | --- | --- | --- | --- | --- |
| BA 主文件 | business documentation | 以業務目的、actor、流程、規則、詞彙與 gaps 說明系統的主要 NotebookLM 來源 | `notebooklm_role: business` | [[notebooklm-ba-knowledge-export]] | business-confirmed |
| Business evidence | 業務證據 | 由 `business_source_paths` 明確指定的需求、流程、決策表或 acceptance spec | 安全文字來源且必須保留 | [[ba-knowledge-precedes-traceability]] | business-confirmed |
| Technical traceability | 技術追溯附錄 | 將 BA 說明連回程式、設定、schema 或工程 Wiki；不是主要業務敘事 | `notebooklm_role: traceability`，可依預算省略 | [[ba-knowledge-precedes-traceability]] | business-confirmed |
| Discovery preflight | 發現預檢 | 第一次唯讀盤點，用來確認 BA coverage 與文件計畫 | ID 不可在 Wiki 更新後 apply | [[readiness-preflight-required]] | business-confirmed |
| Readiness preflight | 就緒預檢 | BA 文件完成後的結構、安全、容量與 identity 驗證 | 成功且第二次確認後才可 apply | [[readiness-preflight-required]] | business-confirmed |
| Knowledge gap | 業務知識缺口 | 無可靠文字證據、互相矛盾或需要 stakeholder 確認的問題 | open／resolved；不得以臆測填補 | [[business-knowledge-gaps]] | business-confirmed |
| Full rebuild | 完整重建 | 移除同一本 Notebook 的舊 static sources，再上傳全部 schema v4 BA-first sources | 舊 retrieval contract migration 必須使用 | [[notebooklm-ba-knowledge-export]] | business-confirmed |

## 詞彙衝突

- `evidence` 在舊 exporter 同時指原始實作來源；新版拆成必要 `business evidence` 與可選
  `technical traceability`，不可再視為同一優先層。
- `ready_to_export` 代表 deterministic readiness gates 通過，不代表所有業務問題已有答案；
  已登記 gaps 可以存在。

## 待確認事項

- NotebookLM tenant UI 對 Custom instructions 的實際名稱與可用性可能依版本／政策不同。


---
title: 業務知識缺口
type: synthesis
summary: NotebookLM BA 知識交付中無可靠證據、尚未建模或需外部確認的事項
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務知識缺口, 待確認, 非文字證據, NotebookLM 驗收]
sources: []
derived_from: ["[[business-process-catalog]]", "[[business-rule-catalog]]", "[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
tags: [synthesis, business-knowledge-gaps, notebooklm]
status: active
---

# 業務知識缺口

| Gap ID | 待確認問題 | 影響流程／規則 | 已查證據 | 建議確認角色 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| `gap-notebooklm-non-text-evidence` | PDF、Office、圖片或訪談中的業務知識由誰轉成可追溯 UTF-8 文字並核准？ | [[notebooklm-ba-knowledge-export]] | v1 workflow 明確不解析這些格式 | BA／PO／文件擁有者 | open |
| `gap-notebooklm-tenant-uat` | 實際 NotebookLM tenant 是否以本 pack 通過固定 BA 題組？ | [[notebooklm-ba-knowledge-export]] | 只有本機結構與 regression tests，尚無 tenant 執行證據 | BA／Notebook owner | open |
| `gap-framework-other-business-processes` | Ingest、Query、Lint、ADR 等一般框架能力是否需要各自建立 BA process/rule pages？ | [[business-process-catalog]] | 目前只有技術功能目錄 | Product owner／BA | open |

## 已解決缺口

目前無。解決後保留原 Gap ID，補上確認來源、日期與結果，不刪除歷史脈絡。


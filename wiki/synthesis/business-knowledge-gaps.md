---
title: 業務知識缺口
type: synthesis
summary: NotebookLM 現況 BA／SA 知識交付與一般 BA／SA／SD 文件中無可靠證據或需外部確認的事項
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務知識缺口, 待確認, 非文字證據, NotebookLM 驗收, 文件 owner, runtime UAT, architecture decision, quality target]
sources: []
derived_from: ["[[business-process-catalog]]", "[[business-rule-catalog]]", "[[notebooklm-ba-knowledge-export]]", "[[business-analysis]]", "[[system-analysis]]", "[[system-design]]"]
last_updated: 2026-09-09
tags: [synthesis, business-knowledge-gaps, notebooklm]
status: active
---

# 業務知識缺口

<!-- codebase-wiki:managed:start -->

| Gap ID | 待確認問題 | 影響流程／規則 | 已查證據 | 建議確認角色 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| `gap-notebooklm-non-text-evidence` | PDF、Office、圖片或其他非 UTF-8 專案內容由誰轉成可追溯文字？ | [[notebooklm-ba-knowledge-export]] | discovery 會列出但不解析這些格式 | BA／SA／文件擁有者 | open |
| `gap-notebooklm-tenant-uat` | 實際 NotebookLM tenant 是否以本 pack 通過固定 BA／SA 題組與治理查核？ | [[notebooklm-ba-knowledge-export]] | 只有本機結構與 regression tests，尚無 tenant 執行證據 | BA／SA／Notebook 管理員 | open |
| `gap-framework-other-business-processes` | Ingest、Query、Lint、ADR 等一般框架能力是否需要各自建立 BA process/rule pages？ | [[business-process-catalog]] | 目前只有技術功能目錄 | Product owner／BA | open |
| `gap-analysis-doc-owner-approval` | BA／SA／SD 的正式 document owner、reviewer 與 profile migration authority 是誰？ | [[generate-analysis-document]]、[[business-analysis]] | Repo 無具名 ownership policy | Project owner | open |
| `gap-analysis-doc-runtime-uat` | 新 BA／SA／SD adapters 在實際 Copilot/Codex host 的 acceptance threshold 是否通過？ | [[generate-analysis-document]]、三份 analysis requirements | Static/unit contract evidence；既有 UAT 未含新 flows | Copilot/Codex platform owners | open |
| `gap-analysis-doc-formal-adr` | 共用 profile、三層 separation 與 marker strategy 是否需要 accepted ADR？ | [[system-design]] | 目前只有 implementation-observed `DE-DOC-*` | Project owner／architect | open |
| `gap-analysis-doc-quality-targets` | 文件產出可接受的 latency、最大 scope 或規模門檻為何？ | [[system-analysis]] `NFR-DOC-006` | 現有 tests 證明功能，不構成 business target | Product owner／platform owners | open |

## 已解決缺口

目前無。解決後保留原 Gap ID，補上確認來源、日期與結果，不刪除歷史脈絡。

`analysis-gap` 不列在本表。它表示納入來源尚未完成分析或缺少 BA／SA pair，readiness
必須阻擋；`evidence-gap` 表示來源已查但仍沒有該事實，`business-confirmation` 表示
程式已證明目前行為但營運政策、責任、核准角色、重跑權限或 SLA 仍需確認。本表只保存
後兩類的 durable gap；不以 `Codebase 未提供證據` 掩蓋尚未完成的追查。
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

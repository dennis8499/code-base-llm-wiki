---
title: 功能需求目錄
type: synthesis
summary: Codebase LLM Wiki 提供給 BA 的 NotebookLM 與 BA／SA／SD 文件 active 功能需求、能力、流程與驗收覆蓋
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [功能需求, functional requirement, capability, 驗收條件, NotebookLM 匯出, BA文件, SA文件, SD文件]
sources: []
derived_from: ["[[overview]]", "[[notebooklm-ba-functional-export]]", "[[business-analysis-document]]", "[[system-analysis-document]]", "[[system-design-document]]"]
last_updated: 2026-09-04
tags: [synthesis, functional-requirements, notebooklm]
status: active
---

# 功能需求目錄

<!-- codebase-wiki:managed:start -->
## Active 功能需求

| Requirement ID | Capability ID | 功能需求 | 主要角色 | 適用流程 | Evidence state | 驗收條件 |
| --- | --- | --- | --- | --- | --- | --- |
| `fr-notebooklm-ba-functional-export` | `cap-notebooklm-ba-functional-export` | [[notebooklm-ba-functional-export]] | 知識維護者、Business Analyst、業務擁有者 | [[notebooklm-ba-knowledge-export]] | implementation-observed | `AC-NBLM-001`–`AC-NBLM-010` |
| `fr-analysis-business-analysis-document` | `cap-analysis-document-generation` | [[business-analysis-document]] | Business Analyst、Product Owner、知識維護者 | [[generate-analysis-document]] | implementation-observed | `AC-DOC-BA-001`–`AC-DOC-BA-006` |
| `fr-analysis-system-analysis-document` | `cap-analysis-document-generation` | [[system-analysis-document]] | System Analyst、stakeholder、知識維護者 | [[generate-analysis-document]] | implementation-observed | `AC-DOC-SA-001`–`AC-DOC-SA-006` |
| `fr-analysis-system-design-document` | `cap-analysis-document-generation` | [[system-design-document]] | Architect、Engineer、Operator、Security reviewer | [[generate-analysis-document]] | implementation-observed | `AC-DOC-SD-001`–`AC-DOC-SD-006` |

## Coverage 摘要

- Active requirements：4
- 已建模流程：[[notebooklm-ba-knowledge-export]]、[[generate-analysis-document]]
- 已建模規則：[[ba-knowledge-precedes-traceability]]、[[readiness-preflight-required]]、
  [[standards-alignment-not-conformance]]、[[missing-evidence-remains-gap]]
- Safe codebase disposition：[[codebase-functional-coverage]]（local-only，不上傳）

## 關聯文件

- [[business-process-catalog]]
- [[business-rule-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

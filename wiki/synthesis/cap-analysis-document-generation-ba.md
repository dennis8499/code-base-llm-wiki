---
title: 分析文件產生 BA
type: synthesis
summary: 依框架現況整理 BA、SA 與 SD 文件產生的角色、流程、規則與結果。
standards_profile: codebase-business-analysis-v1
coverage_status: partial
capability_id: cap-analysis-document-generation
notebooklm_document: ba
notebooklm_group: business-analysis-documents
notebooklm_role: business
notebooklm_terms: [分析文件, BA文件, SA文件, SD文件, user notes, Gap]
sources:
  - .agents/skills/codebase-wiki/references/business-analysis-workflow.md
  - .agents/skills/codebase-wiki/references/system-analysis-workflow.md
  - .agents/skills/codebase-wiki/references/system-design-workflow.md
  - .agents/skills/codebase-wiki/assets/business-analysis-template.md
  - .agents/skills/codebase-wiki/assets/system-analysis-template.md
source_digest: sha256:eaa05ee39535ba2089b267c798531ea0f926144ead95715a1434693419fe6687
source_locators:
  - ".agents/skills/codebase-wiki/references/business-analysis-workflow.md:12"
  - ".agents/skills/codebase-wiki/references/system-analysis-workflow.md:13"
  - ".agents/skills/codebase-wiki/references/system-design-workflow.md:14"
  - ".agents/skills/codebase-wiki/assets/business-analysis-template.md:1"
  - ".agents/skills/codebase-wiki/assets/system-analysis-template.md:1"
derived_from: ["[[business-analysis-document]]", "[[system-analysis-document]]", "[[system-design-document]]", "[[cap-analysis-document-generation-sa]]"]
last_updated: 2026-09-07
tags: [synthesis, business-analysis, codebase-as-is, notebooklm]
status: active
---

# 分析文件產生 BA

<!-- codebase-wiki:managed:start -->
## 功能目的、角色與觸發

使用者以自然語言或對應平台入口明確要求 BA、SA 或 SD 文件時，框架依指定 scope 產生繁體中文 Markdown。主要使用者是 Business Analyst、System Analyst、architect 與知識維護者；明確文件請求即授權相應 Wiki 輸出。

## 流程與規則

1. 依意圖選擇 BA、solution-neutral SA 或 System Design workflow。
2. 先讀 Wiki，證據不足或衝突時才唯讀回溯當下 Codebase。
3. 套用對應 versioned standards profile 與 template，建立 coverage、stable IDs、traceability 和具體 Gap。
4. 重跑時只更新 managed section，保留 `codebase-wiki:user-notes` 原文；legacy SA 首次轉換也保留舊正文。
5. 同步 `wiki/index.md` 並在 append-only `wiki/log.md` 記錄一次 operation，最後執行 Wiki checks。

框架只宣稱依 profiles 組織內容，不宣稱通過 ISO／IEEE conformance 或認證。沒有 stakeholder、政策、target state、KPI、quality target 或上游文件證據時，使用 `Codebase 未提供證據` 或穩定 `gap-*`，不得補造內容。

## 結果、例外與來源衝突

成功結果是預設或 scoped synthesis 文件、可見 coverage 與追溯，以及保留的人工註記。缺少 BA 不阻擋 SA；缺少 SA 不阻擋 SD，但兩者都必須建立上游 Gap。Codebase 未提供各組織的核准者、交付時限或共同品質門檻證據。

本功能的 workflow、prompt 或文件敘述若與實際 templates、validator 或測試衝突，以程式與可執行契約反映的現況為主，並將文字落差列為待更新知識。

## 來源定位

- `.agents/skills/codebase-wiki/references/business-analysis-workflow.md:12`
- `.agents/skills/codebase-wiki/references/system-analysis-workflow.md:13`
- `.agents/skills/codebase-wiki/references/system-design-workflow.md:14`
- `.agents/skills/codebase-wiki/assets/business-analysis-template.md:1`
- `.agents/skills/codebase-wiki/assets/system-analysis-template.md:1`

## 對應 SA

[[cap-analysis-document-generation-sa]]
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## Reviewer Notes

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

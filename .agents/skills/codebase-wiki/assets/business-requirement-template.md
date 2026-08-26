---
title: "{功能需求名稱}"
type: business-requirement
summary: "{哪個角色在什麼條件下需要系統提供什麼可觀察結果}"
requirement_id: "fr-{domain}-{capability}"
capability_id: "cap-{domain}-{capability}"
applies_to: ["[[{business-process-page}]]"]
evidence_state: implementation-observed
notebooklm_group: "business-{capability-slug}"
notebooklm_role: business
notebooklm_terms: ["{功能名稱}", "{角色}", "{業務結果}"]
sources:
  - "{path/to/implementation-evidence}"
derived_from: ["[[overview]]", "[[{business-process-page}]]"]
source_digest: "sha256:{64-lowercase-hex}"
last_updated: YYYY-MM-DD
tags: [business-requirement, notebooklm]
status: active
---

# {功能需求名稱}

<!-- codebase-wiki:managed:start -->
## 業務目的

## 角色與權限

## 前置條件

## 功能行為

| 情境 | 系統行為 | 可觀察結果 | 證據狀態 |
| --- | --- | --- | --- |
| {scenario} | {behavior} | {outcome} | business-confirmed / implementation-observed / inference / gap |

## 業務規則與例外

- [[{business-rule-page}]]

## 輸入、輸出與狀態

## 驗收條件

- `AC-{DOMAIN}-{NNN}`：Given {context}，When {action}，Then {observable-result}。

## 關聯流程

- [[{business-process-page}]]

## 待確認事項

- `gap-{domain}-{topic}`：{question}
<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## BA 補充註記

<!-- 保留人工維護內容；重新萃取時不得覆寫。 -->
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- 原始證據：`{path/to/implementation-evidence}`
<!-- notebooklm:local-only:end -->

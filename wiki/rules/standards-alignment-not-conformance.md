---
title: 標準對齊不等同符合性聲明
type: business-rule
summary: BA／SA／SD 只能宣稱依版本化 profile 組織內容，不得冒稱 ISO／IEEE conformance、認證或稽核通過
rule_id: br-analysis-standard-aligned-not-conformance
applies_to: ["[[generate-analysis-document]]"]
evidence_state: business-confirmed
notebooklm_group: business-analysis-documents
notebooklm_role: business
notebooklm_terms: [standard-aligned, 標準對齊, conformance, ISO, IEEE, IIBA, standards profile]
sources:
  - .agents/skills/codebase-wiki/references/analysis-document-standards.md
source_digest: sha256:da633cacb854b2c680d10ffb2a85cd5943163b0379cd362c833cc4ed56b45db0
derived_from: ["[[generate-analysis-document]]"]
last_updated: 2026-09-04
tags: [business-rule, standards-aligned, governance, notebooklm]
status: active
---

# 標準對齊不等同符合性聲明

<!-- codebase-wiki:managed:start -->

## 規則

BA／SA／SD 文件必須使用已命名、已鎖定版本的 standards profile，並以 standards
mapping 與 coverage evidence 說明如何對齊。文件只能宣稱 `standard-aligned`；不得
宣稱已符合標準全文、獲 ISO／IEEE／IIBA 認證、完成稽核或具有第三方背書。

## 適用條件

- BA：`business-analysis-aligned-v1`（29148:2018 + IIBA v2.0）。
- SA：`system-analysis-aligned-v1`（29148:2018 + 15288:2023 + 25010:2023）。
- SD：`system-design-aligned-v1`（42010:2022 + 25010:2023）。
- IEEE 1016-2009 只可標為 inactive-reserved／informative 歷史組織參考。

## 理由

本框架沒有散布付費標準全文、執行逐條符合性 assessment 或代表 standards body。
Edition 變更也可能改變要求，因此 profile ID 必須 versioned，後續修訂以新 profile
明確遷移。

## 例外與處置

沒有自動例外。組織若需要 conformance claim，必須另取得合法標準內容、定義適用
條款與 objective evidence、指派 reviewer，並把結果記錄為獨立稽核工件，而不是
修改本文件工作流的宣稱。

## 驗收

- `AC-RULE-STD-001`：三份模板皆顯示 profile 與 non-conformance disclaimer。
- `AC-RULE-STD-002`：profile 固定 edition，更新標準不會靜默改變 v1 語意。
- `AC-RULE-STD-003`：1016 不作現行 compliance basis。

<!-- codebase-wiki:managed:end -->

<!-- codebase-wiki:user-notes:start -->
## 業務補充

目前無人工補充。
<!-- codebase-wiki:user-notes:end -->

<!-- notebooklm:local-only:start -->
## 本機追溯

- `.agents/skills/codebase-wiki/references/analysis-document-standards.md`
<!-- notebooklm:local-only:end -->

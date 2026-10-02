---
name: development-spec
description: 釐清功能需求，產生可直接貼入 Issue 給 Megin 的精簡開發規格。
agent: "agent"
argument-hint: "功能敘述、Group 根目錄與適用 Repo"
---

完整載入 `.agents/skills/codebase-wiki/references/development-spec-workflow.md`
與 `.agents/skills/codebase-wiki/assets/development-spec-template.md`。
先讀 `wiki/index.md` 與目前來源確認事實，再逐題詢問必要的業務決策。
使用者未回答的必要問題保持 draft；不得因文件已生成就標為 ready。
依五段模板產生獨立規格，使用 `spec_status` 和 `spec_revision`，不另外
產出 BA／SA／SD。完成後驗證、同步索引並追加 `wiki/log.md`。
Issue 的建立、拆分及指派由使用者自行處理。

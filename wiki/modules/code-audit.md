---
title: Codebase 靜態健檢
type: module
summary: 以唯讀入口追查將可證明的缺陷與待確認業務規則分開，並保存逐入口覆蓋與限制
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/SKILL.md
  - .agents/skills/codebase-wiki/references/code-audit-workflow.md
  - .agents/skills/codebase-wiki/references/frontmatter-spec.md
  - .agents/skills/codebase-wiki/assets/code-audit-template.md
  - .github/prompts/code-audit.prompt.md
  - Codex.md
  - tests/contracts/test_code_audit.py
  - tests/fixtures/code-audit/README.md
  - tests/fixtures/code-audit/expected-findings.md
source_digest: sha256:dc2706bc6fbebcbf822567f2cb192da639e55fc42dacb5c731965eac0ed2fb5b
derived_from: ["[[system-architecture]]", "[[platform-adapters-and-release]]"]
last_updated: 2026-09-16
tags: [module, code-audit, static-analysis, business-logic]
status: active
notebooklm_group: local-governance
notebooklm_role: exclude
---

# Codebase 靜態健檢

## 用途

Engineer 或維護者可以檢查全專案，或限定在特定模組、route、command、job、event 與公開介面，
從入口追到共用服務及可觀察的資料／狀態改變。流程使用靜態閱讀，不執行目標程式、測試、build、
migration 或自動修正；原始碼與設定維持唯讀。

## 判定方式

- `BUG-*` 只用於存在可達觸發條件，且能指出具體錯誤結果或違反明確規則的問題。
- `BIZ-*` 留給尚未定義或含糊的業務政策，附上推論、可能影響與待確認問題。
- 報告的 `sources` 只列實際讀取的原始路徑；有來源時必填並隨重跑更新 `source_digest`，Wiki 證據列入 `derived_from`。
- Severity 依影響描述，與證據確定度分開。共用根因合併，列出所有受影響入口。
- 入口逐一標示 checked、partial 或 not checked；動態路由、外部相依和缺少規格形成明確缺口。
  報告不得把局部無發現解讀成整個專案沒有 BUG。
- 搜尋使用原生工具和直接讀檔；tgrep 仍只限 Ingest／Archaeology。

## 入口與輸出

共享操作為 `code_audit`，明確健檢請求授權寫入
`wiki/synthesis/code-audit-{scope}.md`；全專案 scope 為 `all`。指定「只回報」時不修改 Wiki、
索引或日誌。同範圍重跑沿用 finding IDs 並保留 user-notes 區，未重新檢查的項目維持未確認狀態。
新增或重大更新報告時，連結相關 Wiki 內容、更新 `wiki/index.md`，並追加一筆 `synthesis`
操作到 append-only `wiki/log.md`。

Copilot 使用 `/code-audit [scope]`；Codex 使用自然語言 recipes，兩者皆載入相同 workflow 與
report template。驗收 fixture 涵蓋多入口共享根因、明確規則、業務疑點、上游驗證與動態入口。

## 證據與限制

操作授權與平台映射由 `.agents/skills/codebase-wiki/capabilities.json` 宣告，行為細節由
`.agents/skills/codebase-wiki/references/code-audit-workflow.md` 定義。確定缺陷須有來源位置、
觸發條件、呼叫路徑、影響、修正方向與建議驗證案例；這些是靜態證據，不等於已執行重現。

## 相關頁面

- [[system-architecture]]
- [[platform-adapters-and-release]]
- [[project-function-catalog]]

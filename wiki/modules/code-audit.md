---
title: Codebase 靜態健檢
type: module
summary: 先從目前 Codebase 入口與呼叫路徑追查可證明缺陷，再以定向 Git 歷史和必要的 Wiki 業務規則補充保存逐入口覆蓋與限制
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/SKILL.md
  - .agents/skills/codebase-wiki/references/code-audit-workflow.md
  - .agents/skills/codebase-wiki/references/frontmatter-spec.md
  - .agents/skills/codebase-wiki/assets/code-audit-template.md
  - .agents/skills/codebase-wiki/scripts/validate-code-audit.py
  - .github/prompts/code-audit.prompt.md
  - Codex.md
  - tests/contracts/test_code_audit.py
  - tests/fixtures/code-audit/README.md
  - tests/fixtures/code-audit/expected-findings.md
  - tests/contracts/test_code_audit_validator.py
  - tests/fixtures/code-audit/history/README.md
  - tests/fixtures/code-audit/history/expected-findings.md
source_digest: sha256:3c9579a01cdd5d5b9a7b30b2b424ed622af5edbe4311b8a924669f2ff117aba6
derived_from: ["[[system-architecture]]", "[[platform-adapters-and-release]]"]
last_updated: 2026-09-17
tags: [module, code-audit, static-analysis, business-logic, git-history]
status: active
notebooklm_group: local-governance
notebooklm_role: exclude
---

# Codebase 靜態健檢

## 用途

Engineer 或維護者可以檢查全專案，或限定在特定模組、route、command、job、event 與公開介面，
先從目前 Codebase 的目錄、manifest、設定與註冊處盤點入口，再從入口追到共用服務及可觀察的資料／
狀態改變。Wiki 不決定掃描範圍；只有 source trace 遇到業務規則或政策語意缺口時才查相關頁面，
接著才定向讀取 Git history 的 commit 完整內文與 diff。不執行目標程式、測試、build、migration 或
自動修正，原始碼與設定維持唯讀。
未提交變更也納入目前 source 判定，並在報告中與 HEAD 可達的歷史分開標示。

## 判定方式

- `BUG-*` 只用於存在可達觸發條件，且能指出具體錯誤結果或違反明確規則的問題。
- `RISK-*` 留給有具體技術依據但缺少框架、部署或環境證據的疑點；需列成立條件、缺少證據與確認方式。
- `BIZ-*` 留給尚未定義或含糊的業務政策，附上推論、可能影響與待確認問題。
- 四類固定檢查為 transaction／side effects、configuration references、logic／state contracts、change completeness。
- 交易檢查核對 transaction／connection ownership、write set、commit／rollback、例外、重試與不可回滾的外部副作用；
  設定檢查核對 code reads、鍵名／型別、defaults、產生／注入、部署與 fallback；邏輯檢查核對狀態、回傳與 caller assumptions。
- 報告的 `sources` 只列實際讀取的原始路徑；有來源時必填並隨重跑更新 `source_digest`，Wiki 證據列入 `derived_from`。
- Severity 依影響描述，與證據確定度分開。共用根因合併，列出所有受影響入口。
- 入口逐一標示 checked、partial 或 not checked；動態路由、外部相依和缺少規格形成明確缺口。
  報告不得把局部無發現解讀成整個專案沒有 BUG。
- 入口 inventory 必須來自目前 Codebase 的檔案、manifest、設定與註冊處；既有 Wiki 或舊報告的
  遺漏、過時或缺頁不能排除目前可達入口。動態或外部註冊無法解析時只標記受影響入口的 coverage gap。
- 同一問題若因新證據轉換 BUG／RISK／BIZ 分類，保留原紀錄並以關聯欄位連結新 finding ID；未複查
  的問題維持 `not-rechecked`，歷史分析併入同一份 audit 報告，不另建 Archaeology 報告。
- 搜尋使用原生工具和直接讀檔；tgrep 仍只限 Ingest／Archaeology。

## 入口與輸出

共享操作為 `code_audit`，每次執行都先從目前 Codebase 重新建立入口 inventory；明確健檢請求授權寫入
`wiki/synthesis/code-audit-{scope}.md`；全專案 scope 為 `all`。指定「只回報」時不修改 Wiki、
索引或日誌。同範圍重跑沿用 finding IDs 並保留 user-notes 區，未重新檢查的項目維持未確認狀態。
新增或重大更新報告時，連結相關 Wiki 內容、更新 `wiki/index.md`，並追加一筆 `synthesis`
操作到 append-only `wiki/log.md`；持久化後以 `validate-code-audit.py` 檢查報告結構、finding IDs、
來源存在性、入口關聯、coverage／四類檢查計數與 Git history 的完整 SHA／diff 位置。

Copilot 使用 `/code-audit [scope]`；Codex 使用自然語言 recipes，兩者皆載入相同 workflow 與
report template。驗收 fixture 涵蓋多入口共享根因、交易／設定／介面變更、明確規則、技術風險、
業務疑點、上游驗證、動態入口及可控 Git history。

## 證據與限制

操作授權與平台映射由 `.agents/skills/codebase-wiki/capabilities.json` 宣告，行為細節由
`.agents/skills/codebase-wiki/references/code-audit-workflow.md` 定義。確定缺陷須有來源位置、
觸發條件、呼叫路徑、來源證據、已核對防護／反證、預期與實際行為、影響、修正方向與建議驗證案例；技術風險另須列缺少證據與確認方式；Git
歷史證據必須使用完整 40 字元 SHA、路徑與 diff／blame 位置。這些都是靜態證據，不等於已執行重現。

## 相關頁面

- [[system-architecture]]
- [[platform-adapters-and-release]]
- [[project-function-catalog]]

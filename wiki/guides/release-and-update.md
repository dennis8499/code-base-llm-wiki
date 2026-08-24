---
title: Codebase LLM Wiki — 版本、發佈與更新
type: guide
summary: 以 VERSION、contract 3、CI 與授權 readiness gate 管理可驗證的框架發布
sources:
  - VERSION
  - tools/release.py
  - .github/workflows/release.yml
  - docs/releases/README.md
  - README.md
source_digest: sha256:9737a988c16c03ccec18edf4c77f1735f19ab1880efd63510f3d1a9f2384cc2f
derived_from: ["[[overview]]", "[[platform-adapters-and-release]]"]
last_updated: 2026-08-24
tags: [guide, release, version, extension]
status: active
notebooklm_group: project-guides
---

# Codebase LLM Wiki — 版本、發佈與更新

> 本指南給框架維護者與未來 Extension 作者，說明版號來源、GitHub Release
> 資產與更新 manifest。相關安裝背景請先閱讀 [[framework-introduction]]。

## 版本規則

- `VERSION` 是唯一產品版號來源，格式為穩定 `X.Y.Z`。
- Git tag 必須是 `vX.Y.Z`，且必須與 `VERSION` 完全一致。
- `contract_version: 3` 是 installer contract，不是產品版號。
- Installer 將版號保存至 `.agents/skills/codebase-wiki/VERSION`。
- Framework workflow changes, including the shared Query/Lint follow-up action
  contract, must be reflected in the release documentation, ChangeLog, Wiki
  index, and append-only update log before publishing.

## 發佈流程

1. 更新 `VERSION` 與 `ChangeLog.md`。
2. 由專案擁有者選定並加入明確 `LICENSE`。
3. 執行 `python tools/release.py validate --tag vX.Y.Z`。
4. 推送對應的 `vX.Y.Z` tag。
5. GitHub workflow 執行測試與 Wiki checks。
6. workflow 上傳 ZIP/TAR.GZ、`SHA256SUMS` 與 `update-manifest.json`。

Release builder 會排除 `.git`、`logs`、`.codex-hook-logs`、`.github-hook-logs`、
`cache`、`.venv`、`__pycache__`、`.notebooklm` 與 `dist` 等產生物，也會排除
`.env`、credentials/secrets、private-key path 等敏感檔案。若 `--output` 位於 repo
內，該 output tree 也不會被封裝；installer/NotebookLM transaction journal、lock、
stage、backup 與 temporary sibling files 也不會被封裝；非排除路徑若含 symlink 會 fail closed，避免把
release root 外的內容讀入資產。NotebookLM source pack 是每個使用者本機產生的交付物，
不會混入 framework release。下載資產包含完整 framework Repo，安裝時仍由 installer
選擇 Copilot 或 Codex surface。

`--repository OWNER/NAME` 與 `GITHUB_REPOSITORY` 只接受安全的 GitHub owner/name
元件；不合法的 query、path traversal 或額外 path segment 會被拒絕。

## Extension 更新契約

最新 manifest 固定位於：

`https://github.com/dennis8499/code-base-llm-wiki/releases/latest/download/update-manifest.json`

Extension 的最小流程是：讀取本地 version marker、取得 manifest、比較
`version`、選擇 `assets` 中的格式、驗證 `sha256`，再執行既有 conflict-safe
`upgrade`。遇到人工修改造成的 conflict 時，必須停止更新並保留目標 Wiki。

目前框架只發布 manifest 與本地版本標記，不負責 Extension 的檢查排程、下載
UI 或更新套用邏輯。

目前 Repo 尚未加入 LICENSE；`release.py validate/build` 會明確失敗。這是公開發布
前置條件，不是測試或 installer 錯誤。上游方法論文件只保留原創摘要、作者與來源
連結，未鏡像缺少再散布授權的全文。

## 相關頁面

- [[overview]] — 框架架構、產品結構與版本邊界
- [[framework-introduction]] — 安裝、升級與驗收
- [[platform-adapters-and-release]] — CI、parity 與 release readiness 實作
- [[system-analysis]] — 系統級風險與待確認事項

---
title: Codebase LLM Wiki — 版本、發佈與更新
type: guide
sources:
  - VERSION
  - tools/release.py
  - .github/workflows/release.yml
  - docs/releases/README.md
  - README.md
last_updated: 2026-08-17
tags: [guide, release, version, extension]
status: active
---

# Codebase LLM Wiki — 版本、發佈與更新

> 本指南給框架維護者與未來 Extension 作者，說明版號來源、GitHub Release
> 資產與更新 manifest。相關安裝背景請先閱讀 [[framework-introduction]]。

## 版本規則

- `VERSION` 是唯一產品版號來源，格式為穩定 `X.Y.Z`。
- Git tag 必須是 `vX.Y.Z`，且必須與 `VERSION` 完全一致。
- `contract_version: 2` 是 installer contract，不是產品版號。
- Installer 將版號保存至 `.agents/skills/codebase-wiki/VERSION`。

## 發佈流程

1. 更新 `VERSION` 與 `ChangeLog.md`。
2. 執行 `python tools/release.py validate --tag vX.Y.Z`。
3. 推送對應的 `vX.Y.Z` tag。
4. GitHub workflow 執行測試與 Wiki checks。
5. workflow 上傳 ZIP/TAR.GZ、`SHA256SUMS` 與 `update-manifest.json`。

Release builder 會排除 `.git`、`logs`、`cache`、`.venv`、`__pycache__`、
`.notebooklm` 與 `dist` 等產生物；NotebookLM source pack 是每個使用者本機
產生的交付物，不會混入 framework release。下載資產包含完整 framework Repo，
安裝時仍由 installer 選擇 Copilot 或 Codex surface。

## Extension 更新契約

最新 manifest 固定位於：

`https://github.com/dennis8499/code-base-llm-wiki/releases/latest/download/update-manifest.json`

Extension 的最小流程是：讀取本地 version marker、取得 manifest、比較
`version`、選擇 `assets` 中的格式、驗證 `sha256`，再執行既有 conflict-safe
`upgrade`。遇到人工修改造成的 conflict 時，必須停止更新並保留目標 Wiki。

目前框架只發布 manifest 與本地版本標記，不負責 Extension 的檢查排程、下載
UI 或更新套用邏輯。

## 相關頁面

- [[overview]] — 框架架構、產品結構與版本邊界
- [[framework-introduction]] — 安裝、升級與驗收

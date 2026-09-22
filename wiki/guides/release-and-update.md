---
title: Codebase LLM Wiki — 版本、發佈與更新
type: guide
summary: 以 VERSION、本機驗證、surface-specific ZIP、tag-triggered GitHub Actions 與授權 gate 管理框架發布
sources:
  - VERSION
  - LICENSE
  - .github/workflows/release.yml
  - tools/release.py
  - docs/operations/releases/README.md
  - docs/operations/validation/README.md
  - README.md
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - tests/contracts/test_contracts.py
  - tests/release/test_github_release_workflow.py
  - tests/release/features/github-release.feature
  - tests/release/scenario_runner.py
  - tests/release/test_release.py
  - .agents/skills/codebase-wiki/scripts/validate-code-audit.py
  - .agents/skills/codebase-wiki/bin/tgrep-manifest.json
  - .agents/skills/codebase-wiki/scripts/tgrep-search.py
source_digest: sha256:16cc1ed06e2bd65c4d683747620fdc25f246291e9fc2077caae8b57aa10e97c7
derived_from: ["[[overview]]", "[[platform-adapters-and-release]]"]
last_updated: 2026-09-22
tags: [guide, release, version, extension]
status: active
notebooklm_group: project-guides
notebooklm_role: traceability
---

# Codebase LLM Wiki — 版本、發佈與更新

> 本指南給框架維護者與未來 Extension 作者，說明版號來源、GitHub Release
> 資產與更新 manifest。相關安裝背景請先閱讀 [[framework-introduction]]。

## 版本規則

- `VERSION` 是唯一產品版號來源，格式為穩定 `X.Y.Z`。
- Git tag 必須是 `vX.Y.Z`，且必須與 `VERSION` 完全一致。
- `contract_version: 6` 是 installer/capability contract，不是產品版號。
- Installer 將版號保存至 `.agents/skills/codebase-wiki/VERSION`。
- `.github/workflows/release.yml` 是 framework-only 的正式發版入口，只在符合
  `v*.*.*` 的 tag push 時觸發；installer 不會把它安裝到 target repository。
- Framework workflow changes, including the shared Query/Lint follow-up action
  contract, must be reflected in the release documentation, ChangeLog, Wiki
  index, and append-only update log before publishing.
- Codebase audit changes must keep the source-first entrypoint inventory and
  transaction/configuration/logic/change-completeness checks, targeted Git history
  evidence, report validator, Copilot prompt, and Codex recipe aligned before
  publishing; Wiki pages provide business-rule context only when the source trace
  leaves a policy gap.
- Shared source-discovery changes must also keep the pinned tgrep manifest, wrapper and
  `bundled_tools` release metadata aligned; the integration is limited to Ingest／Archaeology
  and remains independent from other user-facing operations. `code_audit` is an additive v6
  capability; it does not change the installer contract version or product version.

## 發佈流程

1. 更新 `VERSION` 與 `ChangeLog.md`，並確認 `LICENSE` readiness。
2. 在乾淨隔離 worktree，以 Python 3.11 與 3.14 執行 unit、compile、parity、
   frontmatter、stale、log、stats、lint、index checks，並完成人工 semantic review。
3. 執行 `python tools/release.py validate --tag vX.Y.Z` 與
   `python tools/release.py build --output dist --repository OWNER/NAME`，確認
   `codebase-llm-wiki-codex.zip`、`codebase-llm-wiki-copilot.zip`、
   `update-manifest.json`、`SHA256SUMS` 四個資產及 checksum。
4. 將變更合併到 `main`，建立並推送對應 `vX.Y.Z` tag。
5. `.github/workflows/release.yml` 會重新執行 Python 3.11／3.14 validation，並以
   `gh release create --verify-tag --generate-notes` 明列四個資產建立 GitHub Release；
   以下是 workflow 內部的 publish step，維護者不需要手動執行：

```yaml
# .github/workflows/release.yml
run: |
  gh release create "${GITHUB_REF_NAME}" \
    dist/codebase-llm-wiki-codex.zip \
    dist/codebase-llm-wiki-copilot.zip \
    dist/update-manifest.json \
    dist/SHA256SUMS \
    --verify-tag \
    --title "Codebase LLM Wiki ${GITHUB_REF_NAME}" \
    --generate-notes
```

Workflow 不以 `dist/*` 取代四個明列 assets；它只在版本 tag push 時執行，並將
`GITHUB_TOKEN` 限定為建立 Release 所需的 `contents: write`。

Release builder 會排除 `.git`、`logs`、`.codex-hook-logs`、`.github-hook-logs`、
`cache`、`.venv`、`__pycache__`、`.mypy_cache`、`.ruff_cache`、`.notebooklm` 與 `dist` 等產生物，也會排除
`.env`、credentials/secrets、private-key path 等敏感檔案。若 `--output` 位於 repo
內，該 output tree 也不會被封裝；installer/NotebookLM transaction journal、lock、
stage、backup 與 temporary sibling files 也不會被封裝；非排除路徑若含 symlink 會 fail closed，避免把
release root 外的內容讀入資產。NotebookLM source pack 是每個使用者本機產生的交付物，
不會混入 framework release。每個 ZIP 只包含一個 adapter；解壓後使用相同 surface
安裝器命令預覽與套用，若 package surface 與 `--surface` 不一致，installer 會在
寫入前報錯。

`.tgrep/` 是 target repo 的 generated index/server state，release builder 會排除它，
也不由 framework 自動建立或管理。兩個精簡 ZIP 內則包含共用 Skill 的
`scripts/tgrep-search.py`、`bin/tgrep-manifest.json` 與 Windows x64 tgrep 1.0.5；
`update-manifest.json` 透過 `bundled_tools` 記錄 binary path、platform、source URL 與
SHA-256，建置前會 fail closed 驗證 hash。

`--repository OWNER/NAME` 與 `GITHUB_REPOSITORY` 只接受安全的 GitHub owner/name
元件；不合法的 query、path traversal 或額外 path segment 會被拒絕。

## Extension 更新契約

最新 manifest 固定位於：

`https://github.com/dennis8499/code-base-llm-wiki/releases/latest/download/update-manifest.json`

Extension 的最小流程是：讀取本地 version marker、取得 manifest、比較
`version`、選擇 `assets` 中符合 `surface` 的 ZIP、驗證 `sha256`，再執行既有 conflict-safe
`upgrade`。遇到人工修改造成的 conflict 時，必須停止更新並保留目標 Wiki。

目前框架只發布 manifest 與本地版本標記，不負責 Extension 的檢查排程、下載
UI 或更新套用邏輯。

目前 Repo 已加入 MIT `LICENSE`；`release.py validate/build` 仍會明確驗證授權、版本、
tag 與上游 attribution。上游方法論文件只保留原創摘要、作者與來源連結，未鏡像
缺少再散布授權的全文。

## 相關頁面

- [[overview]] — 框架架構、產品結構與版本邊界
- [[framework-introduction]] — 安裝、升級與驗收
- [[platform-adapters-and-release]] — 平台 parity、本機驗證與 release readiness 實作
- [[system-analysis]] — 系統級風險與待確認事項

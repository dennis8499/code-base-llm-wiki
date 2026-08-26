---
title: 平台 Adapter、CI 與 Release
type: module
summary: 以 capability parity、跨平台 CI、單一版本來源與授權前置閘門維持可發布的雙平台框架
notebooklm_group: function-platform-release
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - .github/workflows/ci.yml
  - tools/release.py
  - tests/test_release.py
  - tests/test_contracts.py
source_digest: sha256:2a12ddfa4f4d7578f3b80985c456c78c3f7d439bbd51db03ff9846a1b9362875
derived_from: ["[[system-architecture]]"]
last_updated: 2026-08-24
tags: [module, adapters, ci, release, parity]
status: active
---

# 平台 Adapter、CI 與 Release

## 職責

- 維持 Copilot prompts/agents/hooks 與 Codex recipes/agents/hooks 的共同行為契約。
- 以 `capabilities.json` contract version 3 描述十一個 operations 與 guard modes。
- 在 Linux/Python 3.11、3.14 與 Windows/Python 3.11 執行完整回歸。
- 以根 `VERSION` 作為產品版號唯一來源，產生可驗 hash 的 release assets。
- release assets 排除 `.mypy_cache/`、`.ruff_cache/`、`.codex-hook-logs/`、`.github-hook-logs/` 等平台 fallback/generated state、敏感 credentials/secrets/private-key path 與 repo 內自訂 output tree，並拒絕非排除路徑的 symlink/reparse-point source。
- release builder 在建立或覆寫 artifact 前保留 lexical output boundary，拒絕 output
  root、parent components 與既有 artifact entries 的 symlink/reparse point。
- installer/NotebookLM 的 transaction journal、lock、stage、backup 與 temporary sibling
  artifacts 也不會進 release archive。
- Release manifest 的 repository owner/name 也採嚴格格式驗證，避免下載 URL 被輸入內容污染。
- 在專案擁有者選定 LICENSE 前阻擋公開 release。

## Evidence

- `parity-check.py` 驗證 operations、authorization、hooks、Codex 設定、明確 delegation 與 contract 3。
- `tests/test_contracts.py` 固定 Copilot prompt 必須載入 authoritative workflow reference，並保留
  index/log、confirmation、source schema 與 completion coupling。
- `tests/test_contracts.py` 也固定 CI 的 Ubuntu 3.11/3.14、Windows 3.11 matrix，
  以及 release validate/build/publish gate 宣告；這是 workflow contract evidence，不取代實際 runner。
- `.github/workflows/ci.yml` 執行 unit、parity、frontmatter、stale、log、index 與 lint。
- `tools/release.py` 在 validate/build 時呼叫 `validate_release_readiness()`。
- `tools/release.py` 的 public CLI 先將 stdout/stderr 設為 UTF-8；
  `tests/test_release.py` 以含中文 Windows 路徑的暫存 fixture 驗證 validate/build JSON
  payload 不會因主控台編碼而失敗。
- release CLI 對非 UTF-8 VERSION/history 或 filesystem failure 會回傳受控 validation
  failure，不讓 UnicodeDecodeError/OSError 穿透成未格式化 traceback。
- `docs/history/llm-wiki.md` 只保留原創摘要、作者與 upstream URL，不鏡像無授權全文。

## Contradictions

- `VERSION=0.2.0` 表示實作契約版本已前進，但在 LICENSE 決策完成前不代表已有可公開
  發布的 `v0.2.0` 資產。

## Inferences

- Windows 已執行完整測試，但仍只有 Python 3.11；Linux 提供 Python 3.11/3.14 的雙版本
  覆蓋。

## Gaps

- LICENSE 內容與公開發佈日期是專案擁有者決策。
- 尚未設定套件簽章、SBOM 或 provenance attestation。
- 尚未在實際 Codex/Copilot host 執行互動式 trust、compact 與 audit-context smoke。

## 相關頁面

- [[release-and-update]]
- [[installer-and-upgrade]]
- [[system-analysis]]

---
title: 平台 Adapter、CI 與 Release
type: module
summary: 以 capability parity、跨平台 CI、單一版本來源與授權前置閘門維持可發布的雙平台框架
notebooklm_group: function-platform-release
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/parity-check.py
  - .github/workflows/ci.yml
  - tools/release.py
  - tests/test_release.py
source_digest: sha256:7aaec254f70c82d158669d2580bde06ee0c8e0d25b33c20815a62b9d6d7241e4
derived_from: ["[[system-architecture]]"]
last_updated: 2026-08-21
tags: [module, adapters, ci, release, parity]
status: active
---

# 平台 Adapter、CI 與 Release

## 職責

- 維持 Copilot prompts/agents/hooks 與 Codex recipes/agents/hooks 的共同行為契約。
- 以 `capabilities.json` contract version 3 描述十一個 operations 與 guard modes。
- 在 Linux/Python 3.11、3.14 與 Windows/Python 3.11 執行完整回歸。
- 以根 `VERSION` 作為產品版號唯一來源，產生可驗 hash 的 release assets。
- 在專案擁有者選定 LICENSE 前阻擋公開 release。

## Evidence

- `parity-check.py` 驗證 operations、authorization、hooks、Codex 設定、明確 delegation 與 contract 3。
- `.github/workflows/ci.yml` 執行 unit、parity、frontmatter、stale、log、index 與 lint。
- `tools/release.py` 在 validate/build 時呼叫 `validate_release_readiness()`。
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

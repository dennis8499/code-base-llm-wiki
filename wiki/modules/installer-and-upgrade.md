---
title: Installer 與 Upgrade
type: module
summary: Installer v3 以 dry-run、managed blocks、upstream fingerprints 與原子寫入安全部署雙平台框架
notebooklm_group: function-install-upgrade
sources:
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/references/install-workflow.md
  - .agents/skills/codebase-wiki/assets/target-agents-block.md
  - .agents/skills/codebase-wiki/capabilities.json
  - tests/test_install_framework.py
source_digest: sha256:681278140b48023dfcb28783ec3791346bc02b34b0be8e6673277a9c20441405
derived_from: ["[[system-architecture]]"]
last_updated: 2026-08-21
tags: [module, installer, upgrade, atomicity]
status: active
---

# Installer 與 Upgrade

## 職責

- 在 `install` 與 `upgrade` 前先產生不寫入的變更計畫。
- 只安裝共用 Skill 與選定的 Codex/Copilot adapter；upgrade 不碰目標 Wiki。
- 將 root instructions 放入 managed marker block，保留 marker 外的專案規則。
- 透過 `install-state.json` 分辨 upstream-only、user-only 與 two-sided changes。
- 將所有輸出 staging 後原子替換，失敗時回復原檔。

## 對外介面

```text
install-framework.py install|upgrade
  --target TARGET
  --surface codex|copilot
  --guard-mode wiki-only|coexist
  [--apply]
  [--format json|text]
```

JSON contract version 為 3，包含 `managed`、`changes`、`preserved`、
`conflicts` 與 `obsolete_paths`。沒有 `--apply` 時不修改目標 Repo；存在 conflict
時即使指定 apply 也不套用。

## Evidence

- `_prepare_plan()` 以 manifest baseline 比較目標與新 framework fingerprints。
- `_atomic_write()` 先建立 stage/backup，再使用 `os.replace()` 套用及回復。
- Starter Wiki 日期由注入的 `install_date` 產生，測試不依賴固定系統日期。

## Contradictions

- v0.1 對任意既有 `AGENTS.md` 直接報 conflict；v0.2 將框架區段合併進 managed block。
- 沒有 v3 manifest 的舊目標無法安全推定兩側基線，非 managed file 的差異仍會報 conflict。

## Inferences

- fingerprint manifest 避免了完整三方 merge 的複雜度，但刻意不自動合併同一受管檔案
  內的語意衝突。

## Gaps

- Obsolete paths 只回報，不自動刪除。
- 尚未提供跨版本互動式 conflict resolver。

## 相關頁面

- [[framework-introduction]]
- [[platform-hooks-and-guards]]
- [[platform-adapters-and-release]]
- [[system-analysis]]

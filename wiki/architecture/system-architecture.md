---
title: Codebase LLM Wiki 系統架構
type: architecture
summary: 以共享 Skill 為規格核心，透過雙平台 adapter、標準對齊文件工作流、離線工具與持久 Markdown Wiki 形成可驗證的知識維護系統
notebooklm_group: architecture
notebooklm_role: traceability
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/scripts/lint-wiki.py
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/hooks/common.py
source_digest: sha256:7edd60bed58e9022cd6e63bf98b2ca35956025a0f33940c25cb7984ee0333f69
derived_from: ["[[overview]]"]
last_updated: 2026-09-04
tags: [architecture, framework, data-flow, safety]
status: active
---

# Codebase LLM Wiki 系統架構

## Overview

系統採三層模型：目標專案原始來源是唯讀證據、`wiki/` 是可持續累積的知識層、
`.agents/skills/codebase-wiki/` 與平台 adapter 是行為規格。十一個 machine
operations、十一個 intent groups 與 authorization policy 由
`.agents/skills/codebase-wiki/capabilities.json` 描述，詳細流程由 Skill references
按意圖載入。[[installer-and-upgrade]] 負責把共用規格及選定平台入口安裝到目標 Repo。

## Components

| 元件 | 職責 | 證據 |
| --- | --- | --- |
| Skill 與 references | 意圖路由、授權、不變量、完成條件 | `.agents/skills/codebase-wiki/SKILL.md` |
| Installer v6 | dry-run、managed block、fingerprint manifest、symlink/reparse-safe 原子套用 | `.agents/skills/codebase-wiki/scripts/install-framework.py` |
| BA／SA／SD 文件工作流 | Versioned standards profiles、layer boundary、stable IDs、Gap 與 managed/user/local-only markers | [[business-analysis]]、[[system-analysis]]、[[system-design]] |
| Wiki quality tools | frontmatter、digest freshness、links、index、log 與 lint 狀態 | [[wiki-quality-and-provenance]] |
| Platform hooks | session context、寫入邊界、log reminder | [[platform-hooks-and-guards]] |
| NotebookLM exporter | 完整 discovery、每 capability BA／SA 配對、雙識別碼、DLP、容量與單一 Notebook source plan | [[notebooklm-exporter]] |
| Platform/release surface | Copilot 靜態契約、Codex UAT、本機 gates、版本與手動發布 | [[platform-adapters-and-release]] |

## Data Flow

```text
User intent
  -> SKILL routing + selected workflow
  -> Wiki-first evidence read
  -> BA why/outcome -> SA solution-neutral requirements -> SD design views
  -> authorized Wiki/framework write
  -> frontmatter + digest + index + append-only log checks
  -> full safe discovery + capability/document-gap preview + one confirmation
  -> current-state BA/SA pair regeneration + file disposition + preserved notes
  -> automatic readiness + exact source plan + DLP/capacity checks
  -> apply with confirmed discovery_id + latest preflight_id
  -> documents + query-index / project-map / shared business context / capability upload sources + governance
```

Installer 的資料流是 source framework → dry-run classification → staged writes →
transaction-journaled atomic replacement；Windows stage 繼承 target parent ACL，避免
owner-only temporary DACL 使安裝檔無法由 Codex sandbox account 讀取；遇到兩側同時
變更時不寫入。NotebookLM 先驗證
Wiki regular tree，以明確 `--root` 讀取安全 inventory；discovery ID 只綁定 raw snapshot 與
discovery 設定，文件更新只使 readiness ID 失效。Apply 再次掃描 raw/Wiki、檢查雙 ID 與
output containment，最後原子替換本機 pack。

## Deployment

框架沒有常駐服務或資料庫。執行環境只需要 Python 標準函式庫，以及支援 Codex 或
GitHub Copilot 的專案入口；Git 僅供獨立 Wiki freshness/history 與可選 manifest
provenance 使用，NotebookLM export inventory 與 preflight 不要求 Git。安裝後的
`.notebooklm/` 與 hook logs 是本機生成物，不進入 release。
框架不配置 GitHub Actions；維護者在隔離 worktree 手動驗證，再明列資產建立
GitHub Release。

## Evidence

- `capabilities.json` 是跨平台 machine-readable contract。
- `analysis-document-standards.md` 固定 BA／SA／SD profiles、邊界、coverage 與追溯契約。
- Installer、lint、exporter 與 hooks 皆位於共享 Skill，平台設定只負責調用。
- Canonical installer、lint、exporter 與 hook 程式承載可由測試直接驗證的核心行為。
- Codex CLI 0.152.1 已於 2026-09-03 在獨立 fixtures 完成六項流程各 3/3；
  Copilot 維持 `static-compatible / runtime-unverified`。

## Contradictions

- 舊文件將 guard 稱為 `target`；v0.2.0 將其保留為 `wiki-only` 相容 alias，公開名稱改為
  `wiki-only|coexist|framework`。
- 舊匯出介面允許直接寫入；v0.2.0 起強制 preflight/apply，舊指令預期失敗。

## Inferences

- 無常駐搜尋服務使安裝與稽核面積較小；NotebookLM export 以 Markdown
  `query-index` 對齊 BA／SA capability 路由，但超大型 Wiki 的雲端 retrieval 仍是生成式行為，
  不能視為 deterministic local search。

## Gaps

- 尚未提供 SaaS、NotebookLM API、自動 upload、多租戶權限管理或 Advanced DLP template 同步。
- 公開 Release 仍等待專案擁有者選擇明確 LICENSE。

## Related Pages

- [[overview]]
- [[project-function-catalog]]
- [[business-analysis]]
- [[system-analysis]]
- [[system-design]]
- [[framework-introduction]]

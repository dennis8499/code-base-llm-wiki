---
title: Codebase LLM Wiki 系統架構
type: architecture
summary: 以共享 Skill 為規格核心，透過雙平台 adapter、離線工具與持久 Markdown Wiki 形成可驗證的知識維護系統
notebooklm_group: architecture
sources:
  - .agents/skills/codebase-wiki/capabilities.json
  - .agents/skills/codebase-wiki/scripts/install-framework.py
  - .agents/skills/codebase-wiki/scripts/lint-wiki.py
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/hooks/common.py
source_digest: sha256:8806ab5e6ab1213a1d0458f98cd1be2543cb77be63dd7f530529c639fe7b195a
derived_from: ["[[overview]]"]
last_updated: 2026-08-21
tags: [architecture, framework, data-flow, safety]
status: active
---

# Codebase LLM Wiki 系統架構

## Overview

系統採三層模型：目標專案原始來源是唯讀證據、`wiki/` 是可持續累積的知識層、
`.agents/skills/codebase-wiki/` 與平台 adapter 是行為規格。十一個 machine
operations 與 authorization policy 由
`.agents/skills/codebase-wiki/capabilities.json` 描述，詳細流程由 Skill references
按意圖載入。[[installer-and-upgrade]] 負責把共用規格及選定平台入口安裝到目標 Repo。

## Components

| 元件 | 職責 | 證據 |
| --- | --- | --- |
| Skill 與 references | 意圖路由、授權、不變量、完成條件 | `.agents/skills/codebase-wiki/SKILL.md` |
| Installer v3 | dry-run、managed block、fingerprint manifest、原子套用 | `.agents/skills/codebase-wiki/scripts/install-framework.py` |
| Wiki quality tools | frontmatter、digest freshness、links、index、log 與 lint 狀態 | [[wiki-quality-and-provenance]] |
| Platform hooks | session context、寫入邊界、log reminder | [[platform-hooks-and-guards]] |
| NotebookLM exporter | 全安全範圍盤點、preflight identity、文件優先 source pack | [[notebooklm-exporter]] |
| Release surface | parity、CI、版本、資產與公開發布前置條件 | [[platform-adapters-and-release]] |

## Data Flow

```text
User intent
  -> SKILL routing + selected workflow
  -> Wiki-first evidence read
  -> authorized Wiki/framework write
  -> frontmatter + digest + index + append-only log checks
  -> optional NotebookLM preflight
  -> confirmed apply with matching preflight_id
```

Installer 的資料流是 source framework → dry-run classification → staged writes →
atomic replacement；遇到兩側同時變更時不寫入。NotebookLM 的資料流是 Wiki 與安全
raw inventory → deterministic identity → apply 時重新掃描 → 原子替換本機 pack。

## Deployment

框架沒有常駐服務或資料庫。執行環境只需要 Python 標準函式庫、Git（部分 freshness
與 inventory 能力有 filesystem fallback），以及支援 Codex 或 GitHub Copilot 的
專案入口。安裝後的 `.notebooklm/` 與 hook logs 是本機生成物，不進入 release。

## Evidence

- `capabilities.json` 是跨平台 machine-readable contract。
- Installer、lint、exporter 與 hooks 皆位於共享 Skill，平台設定只負責調用。
- Canonical installer、lint、exporter 與 hook 程式承載可由測試直接驗證的核心行為。

## Contradictions

- 舊文件將 guard 稱為 `target`；v0.2.0 將其保留為 `wiki-only` 相容 alias，公開名稱改為
  `wiki-only|coexist|framework`。
- 舊匯出介面允許直接寫入；v0.2.0 起強制 preflight/apply，舊指令預期失敗。

## Inferences

- 無常駐索引使安裝與稽核面積較小，但超大型 Wiki 的查詢效能仍依賴頁面拆分、分層
  index 與文字搜尋；這是刻意取捨，不是缺少資料庫 migration。

## Gaps

- 尚未提供 SaaS、NotebookLM API、自動 upload 或多租戶權限管理。
- 公開 Release 仍等待專案擁有者選擇明確 LICENSE。

## Related Pages

- [[overview]]
- [[project-function-catalog]]
- [[system-analysis]]
- [[framework-introduction]]

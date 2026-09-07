---
title: Codebase LLM Wiki 專案功能目錄
type: synthesis
summary: 將安裝、Wiki 品質、Hooks、BA／SA／SD、NotebookLM 與發布治理映射到入口、資料、證據與文件覆蓋
notebooklm_group: project
notebooklm_role: traceability
sources: []
derived_from: ["[[overview]]", "[[system-architecture]]", "[[installer-and-upgrade]]", "[[wiki-quality-and-provenance]]", "[[notebooklm-exporter]]", "[[platform-hooks-and-guards]]", "[[platform-adapters-and-release]]", "[[business-analysis]]", "[[system-analysis]]", "[[system-design]]"]
last_updated: 2026-09-04
tags: [synthesis, function-catalog, notebooklm]
status: active
---

# Codebase LLM Wiki 專案功能目錄

## 文件範圍

本目錄以 `scan_profile="framework"` 將共用 Skill、Codex/Copilot adapters 與
release tooling 視為產品證據。Tests、samples、cache、secrets、Wiki 與 export
output 仍依安全 inventory 分類；本機驗證與手動發版行為由專門 Wiki 頁面
引用，而不是當作 NotebookLM raw runtime evidence 自動納入。

## 功能覆蓋矩陣

| 功能域 | 使用者能力 / Use Case | 入口 | 核心資料 | Wiki 頁面 | 覆蓋狀態 |
| --- | --- | --- | --- | --- | --- |
| 安裝與升級 | 安裝 Codex/Copilot surface、安全升級 | `install-framework.py` | install state、file fingerprints | [[installer-and-upgrade]] | covered |
| Wiki 攝取與品質 | 建立可追溯頁面、偵測 stale/link/index/log 問題 | `$codebase-wiki`、quality CLIs | frontmatter、digest、wikilinks、log entries | [[wiki-quality-and-provenance]] | covered |
| 平台 Hooks | 載入 Wiki context、限制寫入、提醒 log | Codex/Copilot hook events | tool payload、guard config、audit output | [[platform-hooks-and-guards]] | covered |
| 分析／設計文件 | 獨立產出 standard-aligned BA、solution-neutral SA 與 SD，建立 Gap-visible 三層追溯 | BA／SA／SD prompt/recipe + shared workflows | profiles、coverage、BA/SR/NFR/IF/DE/VIEW/ADR IDs、markers | [[business-analysis]]、[[system-analysis]]、[[system-design]] | partial |
| NotebookLM 準備 | 全量發現後建立每功能現況 BA／SA，一次確認後產生單一 Notebook 離線 pack | `export-notebooklm.py` | discovery/readiness 雙 ID、BA／SA pair、locator、DLP、容量、manifest v6 | [[notebooklm-exporter]] | covered |
| 平台與發布 | 驗證 Copilot/Codex 契約、建立版本資產 | parity、本機 UAT、`release.py`、`gh` | capability contract、VERSION、checksums | [[platform-adapters-and-release]] | partial |

發布功能標為 partial，原因是本機 builder 與手動程序已具備，但專案擁有者尚未
選擇 LICENSE，公開 release gate 會刻意拒絕建立資產。

## 跨功能能力

| 能力 | 影響範圍 | 主要證據 | 覆蓋狀態 |
| --- | --- | --- | --- |
| Raw-source read-only | 所有 Wiki intents | `AGENTS.md`、`SKILL.md` | covered |
| Untrusted evidence | Ingest、Query、NotebookLM、SA | `SKILL.md`、`ingest-workflow.md` | covered |
| 明確授權 | 十三個 machine operations／十二個 intent groups | `capabilities.json` | covered |
| 原子交付 | Installer、NotebookLM exporter | 兩個 canonical Python modules | covered |
| 跨平台 parity | Copilot、Codex | `parity-check.py` | covered |

## Evidence

- 功能域與公開入口來自上述 module pages 的 raw `sources`。
- 本頁本身不把 Wiki 路徑塞進 `sources`，而以 `derived_from` 保留衍生關係。

## Contradictions

- 舊 exporter 以 architecture/module/function catalog，後續 schema v5 以 BA catalogs 作為
  NotebookLM 主文件；schema v6 改為每 active capability 一組專用 current-state BA／SA，
  並保留 catalogs 與 coverage ledger 作 discovery 及 completeness 基線。

## Inferences

- 現有工程功能域仍可用於 Wiki owner 分工；NotebookLM 的查詢路由由 capability query index、
  project map 與每功能 BA／SA pair 共同定義。

## 未覆蓋與明確排除

- 不提供 RAG、向量資料庫、常駐搜尋 runtime 或自動雲端同步；`query-index` 是匯出的
  Markdown 路由來源，不是本機搜尋服務。
- 缺少 LICENSE、SBOM、簽章與公開 release 實際演練。
- Query 只使用 Wiki 與 Repo source evidence，不提供即時資料庫連線或工具 fallback。

## 相關頁面

- [[overview]]
- [[system-architecture]]
- [[system-analysis]]
- [[business-analysis]]
- [[system-design]]

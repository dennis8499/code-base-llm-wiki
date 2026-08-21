---
title: Codebase LLM Wiki 專案功能目錄
type: synthesis
summary: 將安裝、Wiki 品質、Hooks、NotebookLM 與發布治理映射到入口、資料、證據與文件覆蓋
notebooklm_group: project
sources: []
derived_from: ["[[overview]]", "[[system-architecture]]", "[[installer-and-upgrade]]", "[[wiki-quality-and-provenance]]", "[[notebooklm-exporter]]", "[[platform-hooks-and-guards]]", "[[platform-adapters-and-release]]"]
last_updated: 2026-08-21
tags: [synthesis, function-catalog, notebooklm]
status: active
---

# Codebase LLM Wiki 專案功能目錄

## 文件範圍

本目錄以 `scan_profile="framework"` 將共用 Skill、Codex/Copilot adapters 與
release tooling 視為產品證據。Tests、CI workflow 本身、samples、cache、secrets、
Wiki 與 export output 仍依安全 inventory 分類；測試與 CI 的行為由專門 Wiki 頁面
引用，而不是當作 NotebookLM raw runtime evidence 自動納入。

## 功能覆蓋矩陣

| 功能域 | 使用者能力 / Use Case | 入口 | 核心資料 | Wiki 頁面 | 覆蓋狀態 |
| --- | --- | --- | --- | --- | --- |
| 安裝與升級 | 安裝 Codex/Copilot surface、安全升級 | `install-framework.py` | install state、file fingerprints | [[installer-and-upgrade]] | covered |
| Wiki 攝取與品質 | 建立可追溯頁面、偵測 stale/link/index/log 問題 | `$codebase-wiki`、quality CLIs | frontmatter、digest、wikilinks、log entries | [[wiki-quality-and-provenance]] | covered |
| 平台 Hooks | 載入 Wiki context、限制寫入、提醒 log | Codex/Copilot hook events | tool payload、guard config、audit output | [[platform-hooks-and-guards]] | covered |
| NotebookLM 準備 | 掃描功能、確認後產生離線 pack | `export-notebooklm.py` | inventory、preflight ID、manifest v2 | [[notebooklm-exporter]] | covered |
| 平台與發布 | 驗證 parity/CI、建立版本資產 | parity、CI、`release.py` | capability contract、VERSION、checksums | [[platform-adapters-and-release]] | partial |

發布功能標為 partial，原因是程式與 CI 已具備，但專案擁有者尚未選擇 LICENSE，公開
release gate 會刻意拒絕建立資產。

## 跨功能能力

| 能力 | 影響範圍 | 主要證據 | 覆蓋狀態 |
| --- | --- | --- | --- |
| Raw-source read-only | 所有 Wiki intents | `AGENTS.md`、`SKILL.md` | covered |
| Untrusted evidence | Ingest、Query、NotebookLM、SA | `SKILL.md`、`ingest-workflow.md` | covered |
| 明確授權 | 十一個 machine operations | `capabilities.json` | covered |
| 原子交付 | Installer、NotebookLM exporter | 兩個 canonical Python modules | covered |
| 跨平台 parity | Copilot、Codex | `parity-check.py` | covered |

## Evidence

- 功能域與公開入口來自上述 module pages 的 raw `sources`。
- 本頁本身不把 Wiki 路徑塞進 `sources`，而以 `derived_from` 保留衍生關係。

## Contradictions

- 舊 Wiki 沒有 architecture/module/synthesis 頁，無法滿足 exporter 所宣告的必要文件；
  本次自我攝取已補齊。

## Inferences

- 現有五個功能域是產品能力邊界，而不是單純依目錄切分，因此可用於 NotebookLM
  source grouping 與後續 Wiki owner 分工。

## 未覆蓋與明確排除

- 不提供 RAG、向量資料庫、常駐搜尋 runtime 或自動雲端同步。
- 缺少 LICENSE、SBOM、簽章與公開 release 實際演練。
- SQL Server live evidence 是 Query sub-mode，不是框架本身的資料庫 runtime。

## 相關頁面

- [[overview]]
- [[system-architecture]]
- [[system-analysis]]

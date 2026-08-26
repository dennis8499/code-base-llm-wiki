---
title: Wiki Index
type: index
sources: []
last_updated: 2026-08-26
tags: [index]
status: active
notebooklm_group: wiki-navigation
notebooklm_role: exclude
---

# Codebase Wiki — 索引

> Query 先讀本頁與少量相關頁面；純 Query 與唯讀 Lint 不修改索引。標記內清單由
> `rebuild-index.py` 維護，標記外可保留人工導覽。

## 使用方式

- BA 先從 [[overview]]、[[business-process-catalog]] 與 [[business-rule-catalog]] 理解目的、流程與規則。
- 名詞邊界與未確認事項分別查 [[business-glossary]]、[[business-knowledge-gaps]]。
- 需要實作定位或架構風險時，再進入 [[notebooklm-exporter]]、[[system-architecture]] 與 [[system-analysis]] 技術追溯頁。

<!-- codebase-wiki:index:start -->

## Overview

| 頁面 | 摘要 |
|------|------|
| [[overview]] | 讓知識維護者把 codebase 中的業務流程、規則、詞彙與缺口整理成 BA 可直接詢問的持久 Wiki |

## Business Processes

| 頁面 | 摘要 |
|------|------|
| [[notebooklm-ba-knowledge-export]] | 知識維護者經 discovery 與 readiness 兩次確認，把可追溯業務知識交付給 BA 使用 |

## Business Rules

| 頁面 | 摘要 |
|------|------|
| [[ba-knowledge-precedes-traceability]] | NotebookLM 必須先以業務流程、規則、詞彙與缺口作答，技術細節只能作獨立附錄 |
| [[readiness-preflight-required]] | BA 文件更新後必須重跑 readiness preflight，並以第二次確認的最新 ID 才能產生 pack |

## Architecture

| 頁面 | 摘要 |
|------|------|
| [[system-architecture]] | 以共享 Skill 為規格核心，透過雙平台 adapter、離線工具與持久 Markdown Wiki 形成可驗證的知識維護系統 |

## Modules

| 頁面 | 摘要 |
|------|------|
| [[installer-and-upgrade]] | Installer v3 以 dry-run、managed blocks、upstream fingerprints 與原子寫入安全部署雙平台框架 |
| [[notebooklm-exporter]] | 以 schema v4、BA 結構閘門、必要 business evidence 與獨立 traceability 建立可審查的 NotebookLM source pack |
| [[platform-adapters-and-release]] | 以 capability parity、跨平台 CI、單一版本來源與授權前置閘門維持可發布的雙平台框架 |
| [[platform-hooks-and-guards]] | Codex 與 Copilot 共用 canonical hooks，並以 wiki-only、coexist、framework 三種模式明確控制寫入邊界 |
| [[wiki-quality-and-provenance]] | 以 frontmatter、內容摘要、語意連結、受管索引與 append-only log 建立可稽核的 Markdown 知識層 |

## Entities

_（尚無頁面）_

## Patterns

_（尚無頁面）_

## Decisions

_（尚無頁面）_

## Dependencies

_（尚無頁面）_

## Guides

| 頁面 | 摘要 |
|------|------|
| [[framework-introduction]] | 從安裝、Wiki-first 操作到驗證與升級的框架使用路線 |
| [[notebooklm-export]] | 依 discovery、BA 文件更新、readiness 與第二次確認四階段安全產生離線 source pack |
| [[release-and-update]] | 以 VERSION、contract 3、CI 與授權 readiness gate 管理可驗證的框架發布 |

## Synthesis

| 頁面 | 摘要 |
|------|------|
| [[business-glossary]] | NotebookLM BA 知識交付中的名詞、別名、狀態語意與流程規則關聯 |
| [[business-knowledge-gaps]] | NotebookLM BA 知識交付中無可靠證據、尚未建模或需外部確認的事項 |
| [[business-process-catalog]] | 框架可供 BA 查詢的業務能力、角色、觸發、結果與文件覆蓋 |
| [[business-rule-catalog]] | NotebookLM BA 知識交付的規則、適用流程、證據狀態與例外 |
| [[project-function-catalog]] | 將安裝、Wiki 品質、Hooks、NotebookLM 與發布治理映射到入口、資料、證據與文件覆蓋 |
| [[system-analysis]] | 對框架目的、BA-first NotebookLM contract、介面、安全、維運、風險與證據缺口的技術追溯分析 |

<!-- codebase-wiki:index:end -->

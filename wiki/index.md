---
title: Wiki Index
type: index
sources: []
last_updated: 2026-08-25
tags: [index]
status: active
---

# Codebase Wiki — 索引

> Query 先讀本頁與少量相關頁面；純 Query 與唯讀 Lint 不修改索引。標記內清單由
> `rebuild-index.py` 維護，標記外可保留人工導覽。

## 使用方式

- 從 [[overview]] 了解框架定位，從 [[system-architecture]] 追蹤元件與資料流。
- 從 [[project-function-catalog]] 按功能尋找入口與文件覆蓋。
- 需要跨功能風險、權限、失敗模式時閱讀 [[system-analysis]]。

<!-- codebase-wiki:index:start -->

## Overview

| 頁面 | 摘要 |
|------|------|
| [[overview]] | 以 Wiki-first、唯讀原始證據與共享雙平台規格持續累積可追溯 codebase 知識 |

## Architecture

| 頁面 | 摘要 |
|------|------|
| [[system-architecture]] | 以共享 Skill 為規格核心，透過雙平台 adapter、離線工具與持久 Markdown Wiki 形成可驗證的知識維護系統 |

## Modules

| 頁面 | 摘要 |
|------|------|
| [[installer-and-upgrade]] | Installer v3 以 dry-run、managed blocks、upstream fingerprints 與原子寫入安全部署雙平台框架 |
| [[notebooklm-exporter]] | 以本機 Basic DLP、強制 preflight identity、必要文件閘門與原子輸出建立可審查的增量 NotebookLM source pack |
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
| [[notebooklm-export]] | 先完成功能文件與 DLP preflight，再以相符 ID 原子產生增量 NotebookLM source pack |
| [[release-and-update]] | 以 VERSION、contract 3、CI 與授權 readiness gate 管理可驗證的框架發布 |

## Synthesis

| 頁面 | 摘要 |
|------|------|
| [[project-function-catalog]] | 將安裝、Wiki 品質、Hooks、NotebookLM 與發布治理映射到入口、資料、證據與文件覆蓋 |
| [[system-analysis]] | 對框架目的、元件、流程、介面、安全、維運、風險與證據缺口的整體可追溯分析 |

<!-- codebase-wiki:index:end -->

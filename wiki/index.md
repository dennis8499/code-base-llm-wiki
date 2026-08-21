---
title: Wiki Index
type: index
sources: []
last_updated: 2026-08-21
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
| [[installer-and-upgrade]] | Installer v3 的 managed blocks、fingerprint manifest 與 atomic apply |
| [[wiki-quality-and-provenance]] | Frontmatter、digest、links、managed index 與 append-only log 品質模型 |
| [[notebooklm-exporter]] | 強制 preflight identity 與 documents-first 離線 source pack |
| [[platform-hooks-and-guards]] | Codex/Copilot canonical hooks 與三種 guard mode |
| [[platform-adapters-and-release]] | Capability parity、跨平台 CI、版本與 release readiness |

## Entities

_（尚無需要獨立頁面的 externally exposed entity。）_

## Patterns

_（跨模組模式目前記錄於 architecture 與 modules。）_

## Decisions

_（尚無 ADR。）_

## Dependencies

_（框架沒有執行期第三方套件依賴。）_

## Guides

| 頁面 | 摘要 |
|------|------|
| [[framework-introduction]] | 從安裝、Wiki-first 操作到驗證與升級的框架使用路線 |
| [[notebooklm-export]] | 功能文件化、安全 preflight 與增量 NotebookLM source pack 指南 |
| [[release-and-update]] | VERSION、contract 3、CI、授權與發布資產治理 |

## Synthesis

| 頁面 | 摘要 |
|------|------|
| [[project-function-catalog]] | 五個產品功能域、入口、資料與 coverage 狀態 |
| [[system-analysis]] | 系統目的、流程、介面、安全、失敗模式、風險與 gap |

<!-- codebase-wiki:index:end -->

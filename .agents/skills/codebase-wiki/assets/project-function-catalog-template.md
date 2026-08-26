---
title: 專案功能目錄
type: synthesis
summary: 專案功能域、入口、資料與文件覆蓋的可追溯目錄
notebooklm_group: project
notebooklm_role: traceability
sources: []
derived_from: ["[[overview]]"]
last_updated: YYYY-MM-DD
tags: [synthesis, function-catalog, notebooklm]
status: active
---

# 專案功能目錄

## 文件範圍

說明本次安全掃描包含與排除的工程證據，以及無法驗證的限制。

## 功能覆蓋矩陣

| 功能域 | 使用者能力 / Use Case | 入口 | 核心資料 | Wiki 頁面 | 覆蓋狀態 |
| --- | --- | --- | --- | --- | --- |
| {functional-area} | {capability} | `{entrypoint}` | {data} | [[module-page]] | covered / partial / gap |

## 跨功能能力

| 能力 | 影響範圍 | 主要證據 | 覆蓋狀態 |
| --- | --- | --- | --- |
| {security-or-shared-capability} | {scope} | `path/to/source` | covered / partial / gap |

## 未覆蓋與明確排除

- Tests、CI/CD、IaC、build/dev tooling 不屬於預設 NotebookLM 掃描範圍。
- 列出其他被排除、缺少證據或需要後續 Ingest 的具體路徑。

## 相關頁面

- [[overview]]
- [[system-architecture]]
- [[system-analysis]]

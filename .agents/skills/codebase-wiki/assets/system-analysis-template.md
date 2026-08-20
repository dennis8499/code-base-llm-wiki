---
title: System Analysis Document
type: synthesis
notebooklm_group: system-analysis
sources:
  - wiki/overview.md
last_updated: YYYY-MM-DD
tags: [synthesis, system-analysis]
status: active
---

# System Analysis Document

## 文件資訊

| 項目 | 內容 |
| --- | --- |
| 系統 / 範圍 | {system-or-scope} |
| 產出日期 | YYYY-MM-DD |
| 來源基準 | Codebase LLM Wiki + verified sources |
| 文件狀態 | active / partial |

## 目的與範圍

{Describe why this SA document exists and what is in/out of scope.}

## 讀者與利害關係人

{Describe intended readers, maintainers, operators, product owners, or unknown gaps.}

## 系統總覽

{Summarize the system in evidence-backed prose. Link to [[overview]] or relevant pages.}

## 系統脈絡

{Describe upstream/downstream systems, users, external dependencies, and boundaries.}

## 架構與元件

| 元件 | 職責 | 主要來源 |
| --- | --- | --- |
| {component} | {responsibility} | [[page-name]] / `path/to/source` |

## 模組職責

| 模組 | 職責 | 關聯頁面 |
| --- | --- | --- |
| {module} | {responsibility} | [[module-page]] |

## 主要流程 / Use Cases

### {flow-name}

- 入口：{entrypoint}
- 主要步驟：{steps}
- 輸入 / 輸出：{io}
- 來源：[[page-name]] / `path/to/source`

## API / 介面

| 介面 | 方法 / 事件 | 用途 | 來源 |
| --- | --- | --- | --- |
| {api-or-interface} | {method} | {purpose} | [[entity-page]] / `path/to/source` |

## 資料模型與資料流

{Describe key entities, storage, message payloads, transformations, and data ownership.}

## 外部整合

| 系統 / 套件 | 整合方式 | 風險 / 注意事項 | 來源 |
| --- | --- | --- | --- |
| {dependency} | {integration} | {risk} | [[dependency-page]] |

## 權限與安全

{Describe authentication, authorization, secrets, audit/logging, input validation, or mark gaps.}

## 設定 / 部署 / 維運

{Describe config files, environments, deployment assumptions, jobs, observability, or mark gaps.}

## 非功能需求

| 類別 | 目前證據 | 缺口 |
| --- | --- | --- |
| 效能 | {evidence} | {gap} |
| 可用性 | {evidence} | {gap} |
| 可維護性 | {evidence} | {gap} |
| 安全性 | {evidence} | {gap} |

## 錯誤與失敗模式

{Describe known errors, retries, exception boundaries, fallback behavior, and unknowns.}

## 風險 / 技術債

| 風險 | 影響 | 建議 |
| --- | --- | --- |
| {risk} | {impact} | {recommendation} |

## 待確認事項

- [ ] {gap or question, with suggested wiki/source target}

## 來源附錄

- Wiki: [[page-name]]
- Source: `path/to/source`

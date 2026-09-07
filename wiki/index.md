---
title: Wiki Index
type: index
sources: []
last_updated: 2026-09-07
tags: [index]
status: active
notebooklm_group: wiki-navigation
notebooklm_role: exclude
---

# Codebase Wiki — 索引

> Query 先讀本頁與少量相關頁面；純 Query 與唯讀 Lint 不修改索引。標記內清單由
> `rebuild-index.py` 維護，標記外可保留人工導覽。

## 使用方式

- BA 先從 [[overview]]、[[business-analysis]]、[[business-process-catalog]] 與 [[business-rule-catalog]] 理解目的、流程與規則。
- 名詞邊界與未確認事項分別查 [[business-glossary]]、[[business-knowledge-gaps]]。
- 需求與設計追溯依序查 [[system-analysis]] 與 [[system-design]]；需要實作定位時再進入 [[notebooklm-exporter]] 與 [[system-architecture]] 技術頁。

<!-- codebase-wiki:index:start -->

## Overview

| 頁面 | 摘要 |
|------|------|
| [[overview]] | 讓團隊把 codebase 建成可追溯 Wiki，並產出標準對齊 BA／SA／SD 與現況 NotebookLM BA／SA 知識包 |

## Business Requirements

| 頁面 | 摘要 |
|------|------|
| [[business-analysis-document]] | 使用者可依 Wiki-first 證據獨立產出標準對齊、可追溯且不隱藏缺口的繁中 BA Markdown |
| [[notebooklm-ba-functional-export]] | 將當下完整安全 Codebase 重新萃取成每功能 BA／SA 與單一 Notebook 可用的離線來源包 |
| [[system-analysis-document]] | 使用者可沿用既有 SA 入口產出以系統邊界、需求、介面、品質與驗證為核心的 solution-neutral 分析 |
| [[system-design-document]] | 使用者可將 SA 需求轉成 stakeholders/concerns、架構決策、views、元件、runtime、資料、介面、部署、安全與品質策略 |

## Business Processes

| 頁面 | 摘要 |
|------|------|
| [[generate-analysis-document]] | 使用者以明確請求選擇 BA、SA 或 SD，系統依 Wiki-first 證據產出標準對齊文件、追溯與 Gap |
| [[notebooklm-ba-knowledge-export]] | 知識維護者經全量萃取、一次確認與 readiness 檢核，把現況 BA／SA 交付到單一 Notebook |

## Business Rules

| 頁面 | 摘要 |
|------|------|
| [[ba-knowledge-precedes-traceability]] | NotebookLM source pack 只包含由當下 Codebase 支持的每功能 BA／SA 與導覽，不直接上傳 raw source |
| [[missing-evidence-remains-gap]] | BA／SA／SD 在上游或證據不足時仍產出，但必須建立可追溯 Gap，禁止以推測補滿文字或 Mermaid |
| [[readiness-preflight-required]] | 一次確認鎖定 raw discovery；文件更新後自動重跑 readiness，並以相符雙識別碼產生 pack |
| [[standards-alignment-not-conformance]] | BA／SA／SD 只能宣稱依版本化 profile 組織內容，不得冒稱 ISO／IEEE conformance、認證或稽核通過 |

## Architecture

| 頁面 | 摘要 |
|------|------|
| [[system-architecture]] | 以共享 Skill 為規格核心，透過雙平台 adapter、標準對齊文件工作流、離線工具與持久 Markdown Wiki 形成可驗證的知識維護系統 |

## Modules

| 頁面 | 摘要 |
|------|------|
| [[installer-and-upgrade]] | Installer v6 以 dry-run、managed blocks、upstream fingerprints 與原子寫入安全部署雙平台框架及 BA／SA／SD／NotebookLM current-state 資源 |
| [[notebooklm-exporter]] | 以 schema v6、discovery/readiness identity、BA／SA 配對、DLP 與原子輸出建立單一 Notebook source pack |
| [[platform-adapters-and-release]] | 以 contract v6、Copilot 薄 adapters、Codex recipes、本機 parity 與手動發版維持雙平台框架 |
| [[platform-hooks-and-guards]] | 共用 canonical hooks 以 Git-root 定位與三種 guard modes 維持跨 cwd 寫入邊界 |
| [[wiki-quality-and-provenance]] | 以安全來源解析、內容摘要、受管索引與 append-only log 建立可稽核的 Markdown 知識層 |

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
| [[notebooklm-export]] | 依全量 discovery、一次確認、每功能 BA／SA 與自動 readiness 安全產生 schema-v6 source pack |
| [[release-and-update]] | 以 VERSION、本機驗證、手動 GitHub Release 與授權 gate 管理框架發布 |

## Synthesis

| 頁面 | 摘要 |
|------|------|
| [[business-analysis]] | 讓使用者以獨立、標準對齊且不臆造的 BA／SA／SD 文件工作流建立三層可追溯知識 |
| [[business-glossary]] | NotebookLM 現況 BA／SA 知識交付與一般 BA／SA／SD 文件中的名詞、別名、狀態語意與流程規則關聯 |
| [[business-knowledge-gaps]] | NotebookLM 現況 BA／SA 知識交付與一般 BA／SA／SD 文件中無可靠證據或需外部確認的事項 |
| [[business-process-catalog]] | 框架可供 BA 查詢的 NotebookLM 交付與 BA／SA／SD 文件產出流程、角色、觸發、結果與覆蓋 |
| [[business-rule-catalog]] | NotebookLM 現況 BA／SA 知識交付與一般 BA／SA／SD 文件產出的規則、適用流程、證據狀態與例外 |
| [[cap-analysis-document-generation-ba]] | 依框架現況整理 BA、SA 與 SD 文件產生的角色、流程、規則與結果 |
| [[cap-analysis-document-generation-sa]] | 依框架現況整理分析文件產生的系統邊界、輸入輸出、狀態、介面與失敗行為 |
| [[cap-notebooklm-ba-functional-export-ba]] | 依 exporter 現況整理全量 discovery、一次確認、文件化與單一 Notebook 本機交付 |
| [[cap-notebooklm-ba-functional-export-sa]] | 依 exporter 現況整理 discovery/readiness identity、配對驗證、遮罩、容量與原子輸出 |
| [[codebase-functional-coverage]] | 本機完整性 gate，將 framework scan profile 的每個安全檔案歸屬到 NotebookLM 與 BA／SA／SD 文件功能需求或無可觀察行為 |
| [[functional-requirement-catalog]] | Codebase LLM Wiki 提供給 BA 的 NotebookLM 與 BA／SA／SD 文件 active 功能需求、能力、流程與驗收覆蓋 |
| [[project-function-catalog]] | 將安裝、Wiki 品質、Hooks、BA／SA／SD、NotebookLM 與發布治理映射到入口、資料、證據與文件覆蓋 |
| [[system-analysis]] | 以 solution-neutral 系統邊界、stakeholder needs、SR/NFR/IF 與驗證需求描述 BA／SA／SD 文件能力 |
| [[system-design]] | 以共享 standards profiles、三個文件工作流、雙平台 adapters 與既有驗證／匯出器實作 BA／SA／SD 產出能力 |

<!-- codebase-wiki:index:end -->

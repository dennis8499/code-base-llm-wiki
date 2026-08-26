---
title: 業務流程目錄
type: synthesis
summary: 框架可供 BA 查詢的業務能力、角色、觸發、結果與文件覆蓋
notebooklm_group: business-core
notebooklm_role: business
notebooklm_terms: [業務流程, 業務能力, 知識包, Business Analyst, NotebookLM 匯出]
sources: []
derived_from: ["[[overview]]", "[[notebooklm-ba-knowledge-export]]"]
last_updated: 2026-08-26
tags: [synthesis, business-process-catalog, notebooklm]
status: active
---

# 業務流程目錄

## 文件與證據範圍

本目錄只列出有獨立 BA 流程頁、穩定 process ID、actors、trigger、outcome 與 coverage
狀態的端到端流程。一般 Ingest／Query／Lint 等框架功能目前保留在技術功能目錄，尚未
全部轉成 BA process pages，並已列入 [[business-knowledge-gaps]]。

## 業務流程覆蓋矩陣

| 業務能力 | 流程 ID | 流程 | 主要角色 | 觸發 | 業務結果 | 覆蓋狀態 |
| --- | --- | --- | --- | --- | --- | --- |
| BA 知識交付 | `bp-notebooklm-ba-knowledge-export` | [[notebooklm-ba-knowledge-export]] | 知識維護者、BA、業務擁有者 | 明確要求建立／更新 NotebookLM pack | 經兩次確認的 BA-first source pack | covered |

## 跨流程關係

NotebookLM BA export 會使用一般 Wiki Ingest、index、log、lint 與 source provenance 能力，
但這些是支援活動，不另宣稱為已完整建模的 BA 端到端流程。

## 未覆蓋與明確排除

- 非 NotebookLM 的一般 Wiki 使用旅程尚未拆成 business-process pages。
- NotebookLM 雲端上傳、tenant 管理與回答生成不在本框架自動化範圍。

## 相關頁面

- [[overview]]
- [[business-rule-catalog]]
- [[business-glossary]]
- [[business-knowledge-gaps]]


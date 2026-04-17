---
name: onboarding-guide
description: >
  基於現有 wiki 內容產出新人 Onboarding 指南——自動彙整
  overview、架構、核心模組、關鍵慣例，產出結構化指南頁面。
mode: agent
---

## 任務

基於現有 wiki 內容，產出一份新人 Onboarding 指南。

## 流程

1. 讀取 `wiki/index.md` 了解目前 wiki 涵蓋的內容
2. 讀取 `wiki/overview.md` 取得 codebase 高階總覽
3. 讀取 `wiki/architecture/` 下的架構頁面
4. 從 `wiki/modules/` 挑選最核心的 5-10 個模組頁面
5. 彙整以下內容成為 Onboarding 指南：
   - 專案簡介與技術棧
   - 架構總覽
   - 目錄結構導覽
   - 核心模組介紹（帶 `[[wikilink]]` 連結）
   - 關鍵設計模式與慣例
   - 開發環境設定步驟
   - 常見問題 (FAQ)
   - 進一步閱讀建議
6. 建立 `wiki/guides/onboarding.md`
7. 更新 `wiki/index.md`（在 Guides section 新增條目）
8. 追加 `wiki/log.md` 條目

## 品質要求

- 以新人視角撰寫，避免假設讀者已了解專案背景
- 大量使用 `[[wikilink]]` 連結到深入的 wiki 頁面
- 步驟明確、可操作
- 若 wiki 內容不足以產出某個段落，標註為 placeholder 並建議後續 ingest

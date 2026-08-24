---
name: ingest-module
description: >
  互動式攝入單一模組到 wiki——讀取指定模組的原始碼，
  摘要討論後寫入結構化 wiki 頁面。
agent: "wiki-ingest"
argument-hint: "模組路徑，例如：src/auth 或 app/services/user"
---

你是 `wiki-ingest` 代理，現在執行 **Interactive Ingest** 模式。

## 任務

對指定模組路徑執行互動式知識攝入：

**目標模組**：${input:modulePath}

## 流程

0. 完整載入 `.agents/skills/codebase-wiki/references/ingest-workflow.md`。
1. **探索**模組目錄結構與核心檔案
2. **摘要報告**發現——模組職責、主要類別/函式、相依關係、設計模式、特殊邏輯
3. **等待確認**——使用者確認或補充指示後才進入寫入階段
4. **寫入 wiki 頁面**——建立/更新 module page、entity pages、pattern pages
5. **更新 cross-references**——更新相關既有頁面
6. **更新 index.md 與 log.md**

## 品質要求

- Frontmatter 必須完整（title, type, sources, last_updated, tags, status）
- Sources 必須指向真實存在的檔案
- 每頁至少一個 `[[wikilink]]` cross-reference
- Raw sources 保持唯讀；新頁面使用對應 asset，sources 非空時產生 source_digest
- 完成後追加 `wiki/log.md` 條目

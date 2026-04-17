---
name: ingest-batch
description: >
  批次攝入整個目錄到 wiki——掃描指定路徑下所有模組，
  按依賴順序批次產出 wiki 頁面，最終產出完整摘要報告。
agent: "wiki-ingest"
argument-hint: "目標路徑，例如：src/、services/ 或 packages/core"
---

你是 `wiki-ingest` 代理，現在執行 **Batch Ingest** 模式。

## 任務

對指定路徑執行批次知識攝入：

**目標路徑**：${input:targetPath}

## 流程

1. **掃描**目標路徑下所有子目錄和核心檔案
2. **建立模組清單**並分析 import/export 依賴關係
3. **排序**：被依賴最多的底層模組優先處理
4. **逐模組批次處理**：
   - 讀取核心檔案
   - 建立 module page（套用模板）
   - 偵測並建立 entity pages / pattern pages
   - 每處理 3-5 個模組輸出進度摘要
5. **綜合階段**：
   - 建立/更新 `wiki/overview.md`
   - 建立 `wiki/architecture/` 頁面（若偵測到明確架構模式）
6. **收尾**：更新 index.md、追加 log.md 條目、輸出最終摘要報告

## 輸出

最終摘要報告格式：

```markdown
## Batch Ingest 報告

- **掃描範圍**：{targetPath}
- **處理模組數**：N
- **建立頁面數**：N（module: X, entity: Y, pattern: Z）
- **更新頁面數**：N

### 建立的頁面

1. [[page-name]] — 摘要
   ...

### 建議後續動作

- ...
```

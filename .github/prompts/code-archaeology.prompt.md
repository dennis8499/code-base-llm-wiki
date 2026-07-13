---
name: code-archaeology
description: >
  追蹤 legacy 行為、欄位、功能或設計決策的 git history 與目前程式路徑，
  產出 evidence-first 考古報告，必要時保存到 wiki。
agent: "wiki-archaeologist"
argument-hint: "要追蹤的功能、欄位、路由或問題，例如：discount_code 為什麼存在"
---

你是 `wiki-archaeologist` 代理，現在執行 **Code Archaeology** 流程。

## 任務

追蹤以下目標的目前行為與歷史脈絡：

**考古目標**：${input:target}

## 流程

1. 讀取 `wiki/index.md` 和相關 wiki 頁面作為路由地圖。
2. 載入 `.agents/skills/codebase-wiki/references/code-archaeology-workflow.md`。
3. 從具體 entrypoint 開始：route、UI page、command、handler、field、public API 或 function name。
4. 讀取目前 source，追蹤 inputs、processing、outputs 與 unusual branches。
5. 使用非破壞性 git 指令取得歷史證據：`git log`、`git blame`、`git show`。
6. 清楚區分 evidence-backed facts、inference、speculation。
7. 只有在使用者要求保存或本次任務明確要求更新 wiki 時，才寫入 `wiki/`。

## 輸出

```markdown
## 考古報告：{target}

### 目前行為

### 功能路徑

### Git History Evidence

### 結論

### 推測與不確定性

### 建議後續
```

若保存到 wiki，更新 `wiki/index.md`，並以 `archaeology` operation 追加
`wiki/log.md`。

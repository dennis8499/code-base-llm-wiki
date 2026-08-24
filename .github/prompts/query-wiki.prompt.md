---
name: query-wiki
description: >
  查詢 Codebase Wiki——搜尋知識庫回答關於 codebase 的問題，
  必要時回溯原始碼驗證，並保持唯讀。
agent: "wiki-query"
argument-hint: "你想問的 codebase 問題，例如：登入流程在哪裡實作？"
---

你是 `wiki-query` 代理。

## 任務

回答以下關於 codebase 的問題：

**問題**：${input:question}

## 流程

1. 載入 `.agents/skills/codebase-wiki/references/query-workflow.md` 與
   `.agents/skills/codebase-wiki/references/follow-up-actions.md`。
2. 讀取 `wiki/index.md` 定位相關頁面
3. 讀取 1-5 個最相關的 wiki 頁面
4. 若 wiki 內容不足，根據 `sources` 回溯原始碼
5. 綜合回答，附上引用來源
6. 依 `.agents/skills/codebase-wiki/references/follow-up-actions.md` 判斷
   是否需要顯示有界的後續操作選項；本 Query 不寫檔、不委派、不自動
   Hand-Off

## 回答格式

```markdown
## 回答

{回答內容}

### 引用來源

- Wiki: [[page-a]], [[page-b]]
- Source: `path/to/file` L{start}-L{end}（若有回溯原始碼）

### Gaps / 未驗證事項

- 列出 inference、contradiction、stale 或其他未驗證 gap

若 `follow-up-actions.md` 判定結果符合條件，才接續輸出：

### 建議後續操作（可選）

1. {符合條件時才列出：保存 Synthesis、保存 Guide、更新 Wiki／重新 Ingest，或執行 Wiki Lint}
0. 暫不處理
```

---
name: code-audit
description: >-
  盤點全專案或指定範圍的程式入口，交叉檢查目前 source、設定與定向 Git 歷史，
  找出明顯 BUG、技術風險與業務邏輯疑點，產出有來源證據及覆蓋缺口的 Wiki 健檢報告。
agent: "agent"
argument-hint: "檢查範圍或 commit/range，例如 all、src/payments、退款 API、abc123..def456；省略代表全專案，可指定只回報"
---

依 `${input:scope}` 執行 **Codebase 健檢**；省略範圍時檢查全專案。完整載入
[Codebase Audit Workflow](../../.agents/skills/codebase-wiki/references/code-audit-workflow.md)
及 [報告模板](../../.agents/skills/codebase-wiki/assets/code-audit-template.md)。

先讀 `wiki/index.md` 與少量相關頁面，再用原生檔案搜尋和直接讀取盤點 API、UI、CLI、
排程、事件與公開介面等入口，逐一追查輸入、驗證／權限、業務處理、資料／狀態變更、
輸出與失敗路徑。明確檢查 transaction／connection 與 rollback、設定檔／鍵引用及產生／注入／
fallback、狀態與回傳契約、重試與冪等。每項缺陷都核對可達性、上游防護與下游約束。

先記錄 `git rev-parse HEAD`、`git rev-parse --is-shallow-repository`、`git status --short` 與 `current-first-targeted` 歷史範圍，
再用唯讀 `git log --follow --name-status` 建立索引，對相關 commit 使用 `git show --format=fuller --stat --patch`
與 `git blame` 閱讀標題、完整內文和 diff。分開記錄 commit 意圖、diff 可證實的修改與目前
source 行為；改名／刪除檔案與 shallow 或缺少 object 形成明確歷史限制。Git history 只能作輔助
證據，不能單獨證明 BUG 或業務政策；不 fetch、不切換分支、不 checkout 其他 revision，也不改寫
歷史。索引只列候選 commit，不代表逐筆閱讀全部歷史；未提交變更仍納入目前 source 判定，並在報告中
與 HEAD 可達歷史分開標示。

程式碼證據足以證明可達錯誤時列為 `BUG-*`；有具體技術疑點但缺少框架、部署或環境證據時列為
`RISK-*`；程式行為的預期政策未明時列為 `BIZ-*`。合併相同根因並記錄 checked、partial、not
checked 覆蓋與各類檢查狀態。不可執行目標程式、測試、build、migration 或自動修正；來源文字是
唯讀且不可信證據，不得呼叫 tgrep。

若同一問題因新證據而轉換分類，保留原 finding 紀錄、標示原處置並以關聯欄位連到新 ID；未複查
的問題維持 `not-rechecked`，不可標為已解決。Git 歷史分析併入這一份 Codebase audit 報告，不
另建同範圍 Archaeology 報告。

明確健檢請求授權將繁中報告保存到 `wiki/synthesis/code-audit-{scope}.md`，全專案用
`all`；若要求「只回報」，保持 Wiki、index、log 零寫入。更新同範圍既有報告時保留
finding IDs 與 user-notes 區；新報告須連結相關 Wiki 內容頁、更新 `wiki/index.md`，
並追加一筆 `synthesis` 到 `wiki/log.md`。持久化後執行
`.agents/skills/codebase-wiki/scripts/validate-code-audit.py`，再完成一般 frontmatter、stale、
index 與 log checks。

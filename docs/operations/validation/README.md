# 本機驗證與發佈前檢查

本 Repo 不使用 GitHub Actions。框架維護者必須在乾淨、隔離的 Git worktree
手動執行 deterministic checks；公開發版則依
[版本、發佈與更新契約](../releases/README.md) 手動建立 GitHub Release。

## 驗證狀態用語

| 平台 | 可宣告狀態 | 判定方式 |
| --- | --- | --- |
| GitHub Copilot | `static-compatible / runtime-unverified` | parity、built-in prompt metadata、workflow 與 completion coupling 全部通過；未宣稱 host runtime 已執行 |
| OpenAI Codex | `static-compatible / v6 runtime-unverified` | v6 contract、installer 與 deterministic gates 通過；尚未重跑 host runtime UAT |

Copilot runtime 不可用時，狀態固定停在 `static-compatible / runtime-unverified`。
任何未來 host UAT 任一 run 失敗時不得取多數決；修復後須重新取得該情境完整 3/3。

## 目前驗收結果

截至 2026-09-08 的 v6 驗收以本機 contract、installer、behavior、Wiki governance 與
deterministic suite 為準；Codex host runtime 尚未重跑。2026-09-03 的 v4 Codex CLI 0.152.1
歷史驗收曾在彼此獨立的 Task Tracker Git fixtures
完成 18 個有效 runs：Interactive ingest、Batch ingest、Wiki-first query、Lint、
Code archaeology 與當時仍存在的 Guide 情境各 3/3。這是歷史基線，不代表 Guide 是
目前的 active capability。每個 run 都保存 JSONL tool events、
前後 hashes、Git 狀態、情境 assertions 與 deterministic check 輸出；raw sources
全程不變。證據保存在專用的隔離本機驗收目錄，不提交 session data 或 generated Wiki。

UAT 首輪暴露並修復三項缺口；受影響情境修正後均重新取得完整 3/3：

| 缺口 | 修復與回歸契約 |
| --- | --- |
| Python 3.13+ 的 Windows staging DACL 使安裝檔只對建立者可讀 | Windows stage 改為繼承 target parent ACL，並以 `icacls` regression 驗證已安裝檔具有 inherited ACE |
| `overview.md` 被排除 orphan 檢查時也意外跳過 index completeness | orphan 與 index completeness 分開判斷；overview 缺索引必須回報 `index_missing` |
| 保存 archaeology synthesis 後只由 index/log 連入，造成 semantic orphan | 保存契約要求相關內容頁的語意 inbound wikilink；沒有更適合頁面時由 overview 加入不臆測的 related finding |

## Deterministic checks

從 Repo root 以 Python 3.11 與 3.14 各執行一次：

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .agents/skills/codebase-wiki/scripts tools tests
python .agents/skills/codebase-wiki/scripts/parity-check.py
python .agents/skills/codebase-wiki/scripts/validate-frontmatter.py wiki
python .agents/skills/codebase-wiki/scripts/check-stale.py wiki .
python .agents/skills/codebase-wiki/scripts/validate-log.py wiki/log.md --repo-root .
python .agents/skills/codebase-wiki/scripts/wiki-stats.py wiki
python .agents/skills/codebase-wiki/scripts/lint-wiki.py wiki --repo-root .
python .agents/skills/codebase-wiki/scripts/rebuild-index.py wiki --check
```

`lint-wiki.py` 的 missing-module coverage 與 contradictions 會保持
`agent_review_required`；維護者另行完成人工語意審查並保存結論。另須確認：

- `.github/workflows/` 下沒有 `.yml` 或 `.yaml`；
- 目前文件沒有把 CI 或 tag push 描述成自動發版；
- 所有保留的 Copilot prompts 都使用 built-in `agent` metadata，且 Repo 不含 Wiki
  custom-agent profiles；
- Codex 三個 hooks 可從 repo root、Git 子目錄，以及非 Git 安裝 root 啟動；
- Repo 內 raw-source symlink 可追蹤 resolved target digest，逃逸 Repo 的
  symlink/reparse source 會被拒絕；installer 則拒絕所有 framework-source symlink/reparse。

## BA／SA／SD 文件契約驗收

Contract tests 另固定驗證：

- capability manifest 為 v6、11 operations／11 intent groups，BA／SA／SD 都採
  `explicit_request`；
- 共用 standards reference 鎖定 29148:2018、15288:2023、25010:2023、
  42010:2022 與 IIBA v2.0，IEEE 1016-2009 僅是 informative 歷史參考；
- 三份模板具有正確 `standards_profile`、`coverage_status`、必要章節、穩定 ID、
  coverage/traceability/Gap、Mermaid 槽位及 managed/user-notes/local-only markers；
- SA 是 solution-neutral，首次重跑 legacy SA 的完整原正文保存在 user-notes；
- frontmatter 接受新欄位的合法值、拒絕非法值，同時允許缺少兩欄的 legacy SA；
- NotebookLM schema v6 以 `codebase-ba-sa-v1` 驗證每 capability 的 current-state BA／SA
  pair、雙向連結與 locator，並只把規整後的 `sources/*.md` 列為 upload candidates；
- Codex 與 Copilot installer 都取得共用 references/templates，Copilot 取得三個薄
  prompt adapters，upgrade 不改寫目標 Wiki。

人工語意驗收另逐項確認 `cap/fr/bp/br/AC → SR/NFR/IF → DE/VIEW/ADR` 追溯、
設計內容已由 SA 移到 SD、上游缺失會建立具體 Gap 而不是中止或臆造，以及人工
notes 在重產後保留。

## 五項 active 驗收矩陣

先依 [Task Tracker 樣例](../../../samples/README.md) 把 `samples/task-tracker/`
複製到獨立暫存 Git fixture，再安裝單一平台 surface。

| 功能 | Copilot 靜態契約 | Codex runtime 驗收 |
| --- | --- | --- |
| Interactive ingest | prompt 綁定 ingest workflow 與確認邊界 | 摘要階段零寫入；確認後產生 pages、index 與一筆 ingest log |
| Batch ingest | 選擇 Batch 即授權指定 scope，不重複規則 | 不重問確認；只處理指定 scope，完成 overview、index 與一筆 ingest log |
| Wiki-first query | built-in prompt 綁定唯讀 query workflow | index → 1–5 pages → 必要 sources；答案正確且零寫入 |
| Lint | built-in prompt 綁定 report-before-repair | 注入受控 index 缺口；先報告零寫入，確認後修復並追加一筆 lint log |
| Code archaeology | built-in prompt 綁定 explicit-persist policy | 先解釋目前路徑與 Git evidence；預設零寫入，明確保存後才更新 page、index、log |

自然語言不做 byte-for-byte golden comparison；驗收 evidence、結構、安全邊界與
artifact。每個 Codex 情境在全新 fixture 執行三次，並保存：

- `codex --version`；
- Codex `--json` JSONL tool events 與最後回覆；
- raw `src/`、`config/` 的 before/after SHA-256；
- Wiki before/preview/after hashes；
- deterministic check stdout、stderr、exit code 與情境 assertion 結果。

Interactive Ingest、Lint 與 Archaeology 的 preview/persist 階段必須沿用同一
session；Batch 與 Query 使用明確單次授權。測試證據只放隔離暫存目錄，
不得提交 generated Wiki、hook logs、credentials 或 Codex session data。

## 發佈前清單

- [ ] `git status --short` 只包含預期變更。
- [ ] Python 3.11 與 3.14 的 unit、compile、parity、frontmatter、stale、log、stats、lint、index checks 全部通過。
- [ ] Lint 的 missing-module coverage 與 contradictions 已人工審查。
- [ ] Copilot 標示為 `static-compatible / runtime-unverified`，沒有誤稱 runtime pass。
- [ ] 若宣告 v6 host runtime verified，五個 active 情境各有 3/3 證據；否則維持 `runtime-unverified`。
- [ ] Raw source before/after hashes 相同，Wiki 寫入數與 operation coupling 正確。
- [ ] `.github/workflows/` 沒有 workflow YAML。
- [ ] `wiki/index.md` 已同步，`wiki/log.md` 只追加一筆本次 framework update。
- [ ] ChangeLog 已記錄 durable behavior change。
- [ ] BA／SA／SD contract、frontmatter、NotebookLM、installer 與語意驗收均通過。
- [ ] `VERSION` 是穩定 `X.Y.Z`，發版 tag 嚴格對應 `vX.Y.Z`。
- [ ] 專案擁有者已加入明確 LICENSE；缺少時 release readiness gate 必須阻擋。
- [ ] Release builder 僅先用 fixture 驗證，正式資產通過 manifest 與 SHA-256 檢查。

## 手動語意審查

- Query 確實 Wiki-first，沒有無條件掃描 source tree。
- Copilot prompts 是薄 adapter，且非 VS Code host 不被誤導為支援 prompt files。
- Authorization 沒因 follow-up 或 shell access 擴張。
- Sources、inference、speculation、contradiction 與 gaps 的標示彼此一致。
- Query workflow 與雙平台 adapters 不含即時資料庫存取、資料庫工具或 fallback 指令。
- `.sql`、migration 與 schema 仍可被辨識為唯讀 `data_schema` evidence。

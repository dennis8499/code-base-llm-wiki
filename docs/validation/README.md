# 驗證與發佈檢查

本文件定義 Codebase LLM Wiki 框架 Repo 的 deterministic checks、E2E 驗收與發佈前清單。

## 自動化檢查

從 Repo root 執行：

```powershell
python -m unittest discover -s tests -v
python .agents\skills\codebase-wiki\scripts\parity-check.py
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki
python .agents\skills\codebase-wiki\scripts\lint-wiki.py wiki
python .agents\skills\codebase-wiki\scripts\rebuild-index.py wiki --check
```

| 檢查 | 驗證內容 |
| --- | --- |
| Unit tests | Installer、conflict、surface isolation、guard、Repo links 與 sample contract |
| Parity | Copilot/Codex contract v2、必要入口、移除舊 runtime references |
| Frontmatter | 必填欄位、type、日期、status 與 type-specific contract |
| Stale source | source path 是否存在、tracked source 是否比 Wiki 更新 |
| Wiki stats | Page types、statuses、links 與 Wiki 規模 |
| Wiki lint | Frontmatter、sources、broken links、orphans、index completeness；語意檢查標成 `agent_review_required` |
| Index check | 唯讀比較預期 page/type entries、缺漏、錯區與重複項目 |

## Task Tracker E2E

依 [samples/README.md](../../samples/README.md) 將 `samples/task-tracker/` 複製到暫存目錄，分別驗證 Copilot 與 Codex surface。

每個 surface 至少完成：

1. installer dry-run 與 apply；
2. Ingest `src/task_tracker/`；
3. Query 任務完成與逾期判斷；
4. Lint 產生無 Critical 的報告；
5. 確認 raw source hashes 未改變；
6. 確認新增頁面可由 index 導覽且 log 已追加。

Agent 產出的自然語言不做 byte-for-byte golden comparison；驗收的是 evidence、結構、安全邊界與必要 artifact。

## Predictability Repetition

Copilot 與 Codex 各自重複三次以下情境，驗收 process invariants：

| 情境 | 每次都必須成立 |
| --- | --- |
| Query | index → 1–5 pages → gap sources；零寫入、零自動委派 |
| Interactive Ingest | 探索與摘要完成後才確認寫入；index/log coupling 完整 |
| Lint | deterministic findings 先報告；repairs 等待確認 |
| Delegation | 一般請求留在目前 agent；明確 delegation 才使用 custom agent |

三次輸出可使用不同措辭，但流程不變量必須全部通過。

## 發佈前清單

- [ ] `git status --short` 只包含預期變更。
- [ ] 沒有 `.github/hooks/logs/`、`.codex/hooks/logs/`、`__pycache__/` 或其他執行期 cache 被追蹤。
- [ ] README、docs、samples 與 Codex.md 的本機連結有效。
- [ ] Copilot 與 Codex installer surface 都能在暫存目錄 apply。
- [ ] Installer plan 不包含 `codebase-wiki` 以外的 Skills；upgrade 不包含 `wiki/`。
- [ ] Installer contract 仍是 version 2，CLI 仍只有 `install` 與 `upgrade`。
- [ ] Target config 被轉為 `wiki_guard.mode = "target"`。
- [ ] Framework guard 允許框架文件/樣例/測試，target guard 只允許 `wiki/`。
- [ ] `wiki/index.md` 已同步，`wiki/log.md` 只追加。
- [ ] ChangeLog 已追加本次 durable behavior change。
- [ ] 所有自動化檢查成功，或已明確記錄不可執行原因。
- [ ] SessionStart context 不超過 30 行與 4 KiB UTF-8，且平台設定只引用 canonical hooks。

## 手動檢查重點

- Copilot prompts 與 Codex recipes 表達相同意圖，沒有偽造跨平台功能。
- Query 先使用 Wiki，而不是無條件掃描 source tree。
- SQL Server evidence 規則仍保持 bounded read-only。
- Delegation 仍需使用者明確要求。
- 文件沒有宣告 Repo 尚未具備的 License、RAG、MCP 或 index runtime。

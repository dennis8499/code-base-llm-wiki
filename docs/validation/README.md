# 驗證與發佈檢查

本文件定義 Codebase LLM Wiki 框架 Repo 的 deterministic checks、E2E 驗收與發佈前清單。

## 自動化檢查

從 Repo root 執行：

```powershell
python -m unittest discover -s tests -v
python .agents\skills\codebase-wiki\scripts\parity-check.py
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki
python .agents\skills\codebase-wiki\scripts\validate-log.py wiki\log.md --repo-root .
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki
python .agents\skills\codebase-wiki\scripts\lint-wiki.py wiki
python .agents\skills\codebase-wiki\scripts\rebuild-index.py wiki --check
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --preflight --format json
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --apply --preflight-id ID --output .notebooklm --format json
```

版本發佈前另外執行：

```powershell
python tools\release.py validate --tag v0.2.0
python tools\release.py build --output dist --repository dennis8499/code-base-llm-wiki
```

確認 `dist/` 包含兩種壓縮格式、`update-manifest.json` 與 `SHA256SUMS`，且
manifest 內的版本、tag、下載 URL 與 checksum 全部一致。

| 檢查 | 驗證內容 |
| --- | --- |
| Unit tests | Installer、conflict、surface isolation、guard、Repo links、sample contract、NotebookLM BA schema/full-scan/two-tier evidence export、exclusion-aware fallback pruning/bounded excluded-root summaries、Wiki/CLI root、log regular-tree 與 malformed-state boundaries、process-kill recovery 與跨程序 transaction lock |
| Parity | Copilot/Codex contract v3、guard modes、必要入口、移除舊 runtime references |
| Frontmatter | 必填欄位、type、日期、status、raw/derived provenance、digest，以及 business-requirement/process/rule、FR/AC、NotebookLM role 契約 |
| Stale source | source path、Git freshness 與 aggregate content digest |
| Log integrity | operation、日期、affected pages、frontmatter 與 Git baseline append-only |
| Wiki stats | Page types、statuses、links 與 Wiki 規模 |
| Wiki lint | Deterministic/semantic/overall 狀態、真正 orphan、links、index/log；語意檢查維持 `agent_review_required` |
| Index check | 唯讀比較 managed region 的 page/type entries，並保留 marker 外人工內容 |
| NotebookLM preflight/export | discovery/readiness、七份必備文件、FR/BP/BR/AC 與完整 disposition gate、schema v5、business-only-ba-v2、三階段 DLP masking、exact pack plan、舊 contract full rebuild 與 previous-pack preservation |
| NotebookLM BA UAT | 依 [固定 BA 題組](notebooklm-ba-uat.md) 驗證功能需求、驗收條件、流程、規則、詞彙、gaps、BA 可讀性與 raw evidence absence |

## Task Tracker E2E

依 [samples/README.md](../../samples/README.md) 將 `samples/task-tracker/` 複製到暫存目錄，分別驗證 Copilot 與 Codex surface。

每個 surface 至少完成：

1. installer dry-run 與 apply；
2. Ingest `src/task_tracker/`；
3. Query 任務完成與逾期判斷；
4. Lint 產生無 Critical 的報告；
5. 確認 raw source hashes 未改變；
6. 確認新增頁面可由 index 導覽且 log 已追加。
7. 確認 NotebookLM discovery preflight 零寫入；第一次確認後建立 BA 流程、規則、詞彙與 gaps，再跑 readiness preflight，第二次確認後建立本機 pack 與可操作的 diff plan。
8. Query 對高價值結果顯示有界 follow-up 選項；簡單 Query 不顯示不必要選項。
9. 選擇更新或修復後仍遵守 preview/confirmation；選擇暫不處理時不修改檔案。
10. Installer 與 NotebookLM exporter 在受控 process-kill 後，下一次操作恢復舊內容並清理 transaction journal/stage/backup；另一個程序持鎖時，並行 writer fail closed。

Agent 產出的自然語言不做 byte-for-byte golden comparison；驗收的是 evidence、結構、安全邊界與必要 artifact。

## Predictability Repetition

Copilot 與 Codex 各自重複三次以下情境，驗收 process invariants：

| 情境 | 每次都必須成立 |
| --- | --- |
| Query | index → 1–5 pages → gap sources；符合條件時提供 follow-up options；零寫入、零自動委派 |
| Interactive Ingest | 探索與摘要完成後才確認寫入；index/log coupling 完整 |
| Lint | deterministic findings 先報告；提供受 findings 支持的 options；repairs 等待確認 |
| Delegation | 一般請求留在目前 agent；明確 delegation 才使用 custom agent |
| NotebookLM export | full safe scan → discovery confirmation → BA knowledge update → readiness confirmation → BA-first pack；只手動上傳 changed sources |

三次輸出可使用不同措辭，但流程不變量必須全部通過。

## 發佈前清單

- [ ] `git status --short` 只包含預期變更。
- [ ] 沒有 `.github/hooks/logs/`、`.codex/hooks/logs/`、`__pycache__/` 或其他執行期 cache 被追蹤。
- [ ] README、docs、samples 與 Codex.md 的本機連結有效。
- [ ] Copilot 與 Codex installer surface 都能在暫存目錄 apply。
- [ ] Installer plan 不包含 `codebase-wiki` 以外的 Skills；upgrade 不包含 `wiki/`。
- [ ] Installer contract 是 version 3，plan 列出 managed/changes/preserved/conflicts。
- [ ] Target config 明確使用 `wiki-only` 或 `coexist`；舊 `target` 只作 alias。
- [ ] Framework guard 允許核准 schema/docs/tests/tools；`wiki-only` 只允許 `wiki/`。
- [ ] `wiki/index.md` 已同步，`wiki/log.md` 只追加。
- [ ] `.notebooklm/` 未被納入 release assets；export manifest、stable source IDs、size/word limits 與 upload plan 已檢查。
- [ ] ChangeLog 已追加本次 durable behavior change。
- [ ] 所有自動化檢查成功，或已明確記錄不可執行原因。
- [ ] SessionStart context 不超過 30 行與 4 KiB UTF-8，且平台設定只引用 canonical hooks。
- [ ] Copilot query/lint/archaeology profiles 不暴露直接 `edit`/`agent` tool；需要 shell 的 profile 僅依 instruction 執行 read-only checks/history，且 host permission/sandbox 已阻擋未核准 shell writes。
- [ ] `VERSION` 使用穩定 `X.Y.Z`，且發佈 tag 嚴格符合 `vX.Y.Z`。
- [ ] 專案擁有者已加入明確 LICENSE；未完成時 release readiness gate 必須阻擋。
- [ ] Release assets 已通過 manifest 與 SHA-256 驗證，沒有把 logs/cache 打包。

## 手動檢查重點

- Copilot prompts 與 Codex recipes 表達相同意圖，沒有偽造跨平台功能。
- Query 先使用 Wiki，而不是無條件掃描 source tree。
- SQL Server evidence 規則仍保持 bounded read-only。
- Delegation 仍需使用者明確要求。
- 文件沒有宣告 Repo 尚未具備的 License、RAG、MCP 或 index runtime。

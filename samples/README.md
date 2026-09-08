# Codebase LLM Wiki 五流程 E2E 樣例

`task-tracker/` 是無第三方依賴的 Python codebase，用來驗證 Interactive Ingest、
Batch Ingest、Wiki-first Query、Lint 與 Code Archaeology。所有 runtime
測試都在 Repo 外的全新暫存 Git fixture 執行，不能直接污染版本化樣例。

## 準備每一次 fixture

PowerShell：

```powershell
$sampleTarget = Join-Path ([System.IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
Copy-Item -LiteralPath samples\task-tracker -Destination $sampleTarget -Recurse
git -C $sampleTarget init -q
git -C $sampleTarget add .
git -C $sampleTarget -c user.email=wiki@example.com -c user.name=Wiki commit -qm initial
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target $sampleTarget --surface codex --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target $sampleTarget --surface codex --apply --format json
Get-ChildItem -LiteralPath (Join-Path $sampleTarget 'src'), (Join-Path $sampleTarget 'config') -File -Recurse |
  Get-FileHash -Algorithm SHA256 | Sort-Object Path
```

macOS / Linux 使用 `mktemp -d`、`cp -R` 與相同的 `git -C`、installer commands。
每個情境、每次 repetition 都必須用不同目錄。保存初始 raw hashes、
`codex --version` 與 Codex `--json` JSONL；完成後再比對 hashes。

## GitHub Copilot 靜態驗證

Copilot runtime 不屬於目前可用驗證環境，因此本 Repo 只標示
`static-compatible / runtime-unverified`。以 `--surface copilot` 安裝到另一份 fixture，
再執行 parity 與 unit tests，確認：

- `.github/prompts/` 的 active 入口是連結共用 workflow 的薄 adapter；這些 prompt files
  只適用 VS Code 本機 Agent host；
- 其他 Copilot hosts 改由 `.agents/skills/codebase-wiki/` 接收自然語言意圖；
- Interactive/Batch authorization、Query 零寫入、Lint report-first、Archaeology
  explicit persist 都被 parity 固定，且 prompts 使用 built-in `agent` metadata。

這些檢查不能被描述為 Copilot runtime pass。

## Codex 五項情境

每項在獨立 fixture 執行三次。Interactive Ingest、Lint 與 Archaeology 的兩階段
操作必須沿用同一 session。

### 1. Interactive Ingest

```text
使用 $codebase-wiki 以 Interactive Ingest 分析 src/task_tracker/。先只摘要職責、
公開介面、相依性、狀態轉換、特殊分支與風險；不要寫入，等待我確認。
```

保存 preview 後的 Wiki hashes，確認完全不變，再於同一 session 回覆：

```text
確認，請依剛才的摘要寫入 Wiki，完成 pages、source_digest、wikilinks、index，
並只追加一筆 ingest log。
```

### 2. Batch Ingest

```text
使用 $codebase-wiki 對 src/task_tracker/ 執行 Batch Ingest。這個請求已授權指定
scope，不要再次詢問確認；不得處理 scope 外 raw sources。完成 overview、pages、
index，並只追加一筆 ingest log。
```

驗證沒有重問、沒有 scope expansion，且 overview/index/log coupling 完整。

### 3. Wiki-first Query

先以已驗證的 ingest 結果建立 fixture baseline，再清除 session，記錄 Wiki hashes：

```text
使用 $codebase-wiki 先讀 wiki/index.md，再讀最多五個相關頁面，只有必要時回溯
sources：TaskTrackerService.complete_task 遇到不存在與已完成任務各如何處理？
逾期如何判定？請列 evidence 與 gaps，不要寫檔。
```

答案應涵蓋 not-found、duplicate completion 與 overdue evidence；Wiki hashes 必須不變，
JSONL 不得出現 write tool。

### 4. Lint

在已 ingest 的 fixture 刪除 `wiki/index.md` managed region 中一個實際 page entry，
提交這個受控 defect，再執行：

```text
使用 $codebase-wiki 執行 Wiki Lint。先回報 deterministic 與 semantic findings，
不要修復，等待我確認。
```

確認 preview 零寫入後，在同一 session 回覆：

```text
確認，只修復剛才報告的 index 缺口，並只追加一筆 lint log。
```

### 5. Code Archaeology

```text
使用 $codebase-wiki 考古 TaskTrackerService.complete_task。先說明目前 code path，
再用非破壞性的 git log、git blame、git show 補歷史證據；預設不要寫入。
```

確認 Wiki hashes 不變、回答區分 evidence/inference 後，在同一 session 明確要求：

```text
請把剛才的考古結果保存為 durable Wiki page，更新 index，並只追加一筆
archaeology log。
```

## 每次 deterministic checks

在 fixture root 執行：

```powershell
python .agents/skills/codebase-wiki/scripts/validate-frontmatter.py wiki
python .agents/skills/codebase-wiki/scripts/check-stale.py wiki .
python .agents/skills/codebase-wiki/scripts/validate-log.py wiki/log.md --repo-root .
python .agents/skills/codebase-wiki/scripts/wiki-stats.py wiki
python .agents/skills/codebase-wiki/scripts/lint-wiki.py wiki --repo-root .
python .agents/skills/codebase-wiki/scripts/rebuild-index.py wiki --check
```

每次保存 command、stdout、stderr、exit code 與 assertion 結果。任一次失敗就不判定
該情境通過；修正後重跑完整 3/3。Raw `src/` 與 `config/` before/after hashes
必須完全相同。完整框架 gates 見[本機驗證手冊](../docs/operations/validation/README.md)。

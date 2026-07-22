# Codebase LLM Wiki E2E 樣例

`task-tracker/` 是一個無第三方依賴的 Python codebase，用來手動驗證 Codebase LLM Wiki 的 Installer、Ingest、Query、Lint、index/log 維護與 raw-source protection。

## 為什麼先複製到暫存目錄

Installer 會把 `.agents/`、平台入口與 `wiki/` 寫入目標 Repo。直接對版本化的 `samples/task-tracker/` 執行 `--apply` 會污染樣例，因此必須先複製到 Repo 外的暫存位置。

## 準備樣例

PowerShell：

```powershell
$sampleTarget = Join-Path ([System.IO.Path]::GetTempPath()) 'codebase-wiki-task-tracker'
Copy-Item -LiteralPath samples\task-tracker -Destination $sampleTarget -Recurse
Get-ChildItem -LiteralPath (Join-Path $sampleTarget 'src'), (Join-Path $sampleTarget 'config') -File -Recurse |
  Get-FileHash -Algorithm SHA256 |
  Sort-Object Path
```

macOS / Linux：

```bash
sample_target="$(mktemp -d)/codebase-wiki-task-tracker"
cp -R samples/task-tracker "$sample_target"
find "$sample_target/src" "$sample_target/config" -type f -exec sha256sum {} \; | sort
```

請選擇新的空路徑；若同名目錄已存在，改用另一個名稱，不要覆寫既有資料。保存初始 hashes，完成 Agent workflow 後再次比對。

## 驗證 Copilot surface

在框架 Repo root 執行：

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target $sampleTarget --surface copilot --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target $sampleTarget --surface copilot --apply --format json
```

以 VS Code 開啟 `$sampleTarget`，在 Copilot Chat Agent mode 依序執行：

```text
請分析 src/task_tracker/。先摘要職責、公開介面、相依性、狀態轉換、特殊分支與風險；
確認後建立或更新 wiki pages、wikilinks、wiki/index.md，並追加 wiki/log.md。
```

```text
請先查 wiki，再必要時回溯 sources：
TaskTrackerService.complete_task 遇到不存在與已完成的任務各會怎麼處理？逾期任務如何判定？
```

```text
請依 lint 流程檢查 wiki 的 frontmatter、source paths、wikilinks、index completeness 與 stale 狀態，先列出 findings，不要直接做廣泛修復。
```

## 驗證 Codex surface

使用另一份乾淨的樣例副本，避免 Copilot 與 Codex 安裝檔互相干擾：

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target $sampleTarget --surface codex --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target $sampleTarget --surface codex --apply --format json
```

以 Codex 開啟目標目錄，使用與上一節相同的三段自然語言要求。Codex 應讀取 `AGENTS.md` 與 `$codebase-wiki`，不需要 project-level slash prompt。

## 預期結果

Agent 產出的頁面名稱可以不同，但必須滿足以下行為契約：

- `wiki/index.md` 能導覽到 Task Tracker module 與關鍵 entity/service pages。
- Wiki 說明 `TaskItem`、`TaskStatus`、`TaskRepository`、`InMemoryTaskRepository`、`TaskTrackerSettings` 與 `TaskTrackerService` 的關係。
- Query 正確指出 not-found、duplicate completion、open-task limit 與 overdue 判斷，並引用對應 Wiki/source evidence。
- 每個新增 Wiki page 的 frontmatter.sources 指向真實的 `src/task_tracker/` 或 `config/` 路徑。
- Ingest 後 `wiki/log.md` 只追加新條目。
- Lint 沒有 Critical；若有 coverage gaps，必須明確列出而不是虛構內容。
- `src/` 和 `config/` 的 hashes 與執行前相同。

## Deterministic checks

在樣例目標目錄執行：

```powershell
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki
```

框架 Repo 的完整發佈檢查請看 [驗證手冊](../docs/validation/README.md)。

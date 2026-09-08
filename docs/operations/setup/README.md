# 安裝、升級與平台設定

本文件涵蓋 Codebase LLM Wiki 的兩種安裝 surface、guard mode、升級與常見問題。架構背景請看 [架構文件](../../product/architecture/README.md)。

## 前置需求

- Git
- Python 3.11 或更新版本
- 欲使用 Copilot surface：VS Code 與 GitHub Copilot Chat
- 欲使用 Codex surface：OpenAI Codex CLI、IDE extension、App 或 Cloud task

Installer 不需要 PyYAML、Node.js、資料庫、向量模型或其他第三方套件。

目標專案的 `wiki/` 由共用 Skill 內的乾淨 starter 建立；框架 Repo 自己的 Wiki pages 與活動歷史不會被複製。
Installer allowlist 只包含 `.agents/skills/codebase-wiki/`，不會複製同一
工作目錄中的其他個人或 workspace Skills。

## Dry-run 優先

所有安裝與升級都先執行 dry-run。Contract v6 JSON 回應包含 `managed`、
`changes`、`preserved`、`conflicts`、`obsolete_paths` 與 `applied`；只有
`--apply` 且 `conflicts` 為空時才以 staged atomic write 套用。Installer 會留下
active/committed transaction journal；若程序在替換窗口終止，下一次 apply 會先恢復
原檔並清理暫存 stage/backup。同一 target 的並行 apply 會由 sibling transaction lock
序列化；若已有程序持鎖，後來的寫入會 fail closed，不會覆蓋前一個 journal。
Windows stage 會繼承 target parent ACL，避免 Python 3.13+ 的 owner-only temporary
directory DACL 被安裝檔保留，導致 Codex sandbox account 無法讀取已安裝 surface。

### GitHub Copilot surface

PowerShell：

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\target --surface copilot --guard-mode wiki-only --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\target --surface copilot --guard-mode wiki-only --apply --format json
```

macOS / Linux：

```bash
python3 .agents/skills/codebase-wiki/scripts/install-framework.py install --target /path/to/target --surface copilot --guard-mode wiki-only --format json
python3 .agents/skills/codebase-wiki/scripts/install-framework.py install --target /path/to/target --surface copilot --guard-mode wiki-only --apply --format json
```

Copilot surface 安裝 `AGENTS.md`、`.agents/`、`.github/` 與 `wiki/`，不安裝 `.codex/` 或 `Codex.md`。

### OpenAI Codex surface

PowerShell：

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\target --surface codex --guard-mode wiki-only --format json
python .agents\skills\codebase-wiki\scripts\install-framework.py install --target C:\path\to\target --surface codex --guard-mode wiki-only --apply --format json
```

macOS / Linux：

```bash
python3 .agents/skills/codebase-wiki/scripts/install-framework.py install --target /path/to/target --surface codex --guard-mode wiki-only --format json
python3 .agents/skills/codebase-wiki/scripts/install-framework.py install --target /path/to/target --surface codex --guard-mode wiki-only --apply --format json
```

Codex surface 安裝 `AGENTS.md`、`Codex.md`、`.agents/`、`.codex/` 與 `wiki/`，不安裝 `.github/`。

## Guard mode

| Mode | 使用位置 | 允許的 Wiki 任務寫入 |
| --- | --- | --- |
| `wiki-only` | 安裝框架的安全預設 | 僅 `wiki/` |
| `coexist` | 一般 coding 與 Wiki 共存 | Repo 內明確 edit；非 Wiki path 回傳 audit context |
| `framework` | Codebase LLM Wiki 框架 Repo 本身 | Wiki、schema、adapters、docs、samples、tests、tools 與核准 root files |

Installer 預設把 framework 設定轉成 `wiki-only`；舊 `target` 值會相容映射至
`wiki-only`。需要同一工作階段進行正常 coding 時，安裝時明確選擇
`--guard-mode coexist`。任何 mode 都不會改變 Wiki task 的 raw-source 唯讀規則。

## 升級

將 `install` 改成 `upgrade`，仍先 dry-run：

```powershell
python .agents\skills\codebase-wiki\scripts\install-framework.py upgrade --target C:\path\to\target --surface codex --guard-mode wiki-only --format json
```

- `.agents/skills/codebase-wiki/install-state.json` 保存 upstream fingerprints。
- Upstream-only 變更自動更新；user-only 變更列為 `preserved`。
- Local 與 upstream 同時變更才列入 `conflicts`，整次 apply 不執行。
- `AGENTS.md` 與 Copilot instructions 只更新 managed marker block，保留其餘內容。
- `upgrade` 只規劃 framework surface，既有 `wiki/` 不參與 conflict
  判斷且保持 byte-for-byte 不變。
- Installer 不做語意三方 merge，也沒有 `--force`；套用失敗會 rollback。
- `.codebase-wiki/` 只會出現在 `obsolete_paths`；確認沒有人工內容後由維護者另行處理。

## 平台啟用

### GitHub Copilot

1. 以 VS Code 開啟目標 Repo。
2. 確認 Copilot Chat 可使用 Agent mode 與 repository custom instructions。
3. 依 VS Code 信任流程允許專案 hooks。
4. 使用自然語言或 `.github/prompts/` 的 prompts。

`.github/prompts/` 只屬於 VS Code 本機 Agent host。GitHub Copilot coding agent
或其他 Copilot hosts 應以自然語言使用 `.agents/skills/codebase-wiki/`；不要把
prompt files 當成跨 host API。保留的 prompts 使用 VS Code built-in `agent`
metadata；框架不安裝 Repo-local Wiki agent profiles。

### OpenAI Codex

1. 以 Codex 開啟目標 Repo，確認 `AGENTS.md` 被讀取。
2. 確認 `.agents/skills/codebase-wiki/SKILL.md` 可被發現。
3. 在 `/hooks` 或產品對應介面信任 project-local hooks。
4. 需要完整 recipes 時閱讀根目錄 `Codex.md`。

## NotebookLM Enterprise source pack

NotebookLM export 是服務 BA 與 SA 的離線產出流程，不需要 API credentials，也不會由
installer 自動啟用或上傳檔案。從 Repo root 先執行唯讀 discovery preflight：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --preflight --format json
```

Agent 掃描完整安全 UTF-8 repo text（包含 behavioral tests、README、規格與註解），盤點
FR/AC、actor、流程、規則、詞彙、證據狀態與 gaps。預覽必須列出 inventory、每功能 BA／SA
coverage、待分析內容、容量與未驗證事項；即使沒有警告也要等待一次確認。確認後補齊
catalogs、完整 file disposition ledger 與每個 `cap-*` 的 BA／SA 配對，記錄 analyzed discovery
ID，再自動執行 readiness `--preflight` 與 apply：

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --apply --discovery-id <confirmed-discovery-id> `
  --preflight-id <readiness-id> --output .notebooklm --format json
```

Exporter 產生完整 `documents/{cap}-ba.md`／`-sa.md`、只供上傳的 `sources/*.md`、schema v6
`manifest.json`、`upload-plan.md`、README 與 local-only governance。Raw source/config 不會直接
進入 pack；documents 與 sources 的 DLP finding 先遮罩，residual 有命中才阻擋。
只把 `sources/*.md` 手動加入企業版 Notebook；再次執行時仍會全量重掃專案與增量
更新 Wiki，再依 upload plan 處理新增、變更與刪除，`unchanged` 不需重新上傳。
`.notebooklm/` 預設被 Git 忽略；若需調整 Workspace tier 或 analysis scope，可將
`.agents/skills/codebase-wiki/assets/notebooklm.toml` 複製為 Repo root 的
`notebooklm.toml` 後修改。

## 常見問題

### 回報 conflicts

先閱讀 JSON 中的精確路徑。`preserved` 是安全保留的 user-only 變更；只有
`conflicts` 需要人工合併，完成後重新 dry-run。

### Hooks 沒有執行

- 確認 Python 可用。
- 確認平台已信任 project-local hooks。
- Codex 檢查 `.codex/config.toml` 的 hooks feature。
- Copilot 檢查 `.github/hooks/` 設定與 VS Code 支援版本。
- 修改設定後重啟平台工作階段。
- Codex 從 Git 子目錄啟動時，確認 `.codex/hooks.json` 能以
  `git rev-parse --show-toplevel` 找到 canonical scripts；非 Git 安裝 root 才回退
  session cwd。

### Write guard 阻擋變更

- `wiki-only` 的 Wiki 任務只能寫 `wiki/`，這通常是正確行為。
- 若一般 coding 與 Wiki 必須共存，重新安裝／升級並明確選擇 `coexist`。
- 框架 Repo 維護才使用 `framework` mode。
- 若需求是修改應用程式原始碼，請結束 Wiki 任務並改成一般 coding task。

### Skill 沒有觸發

- 確認 `.agents/skills/codebase-wiki/SKILL.md` 存在。
- Codex 可明確輸入 `$codebase-wiki`。
- Copilot 可選擇對應 Agent 或 prompt。
- 新增 skill 後重新開啟工作階段。

## 安裝後驗證

```powershell
python .agents\skills\codebase-wiki\scripts\parity-check.py
python .agents\skills\codebase-wiki\scripts\validate-frontmatter.py wiki
python .agents\skills\codebase-wiki\scripts\check-stale.py wiki .
python .agents\skills\codebase-wiki\scripts\validate-log.py wiki\log.md --repo-root .
python .agents\skills\codebase-wiki\scripts\lint-wiki.py wiki
python .agents\skills\codebase-wiki\scripts\wiki-stats.py wiki
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --preflight --format json
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py --root . --apply --discovery-id DISCOVERY_ID --preflight-id PREFLIGHT_ID --output .notebooklm --format json
```

完整的框架 Repo 發佈檢查請看 [驗證手冊](../validation/README.md)。

# 版本、GitHub Actions 發佈與更新契約

## 版本來源與 readiness gate

產品版號唯一來源是 Repo 根目錄的 `VERSION`，格式為穩定 SemVer
`MAJOR.MINOR.PATCH`；目前版號是 `0.3.0`。Git tag 必須是完全對應的
`vX.Y.Z`。Installer 產生的 `.agents/skills/codebase-wiki/VERSION` 是目標 Repo
的本地版本標記；`contract_version: 6` 則是獨立的 installer/API contract。

本 Repo 採用 MIT License。`tools/release.py validate` 與 `build` 會在建立正式資產前
驗證授權、版本與上游 attribution readiness。不得用參數或修改 fixture 以外的資料
繞過此 gate。

## 目前正式版本：v0.3.0

Codebase LLM Wiki v0.3.0 已於 2026-10-03 發布，來源 tag 指向
[`538712f`](https://github.com/dennis8499/code-base-llm-wiki/commit/538712f553457d53b8e451d1733fe97a01c6aff6)。
已通過 Python 3.11 與 3.14 release checks；[正式 Release](https://github.com/dennis8499/code-base-llm-wiki/releases/tag/v0.3.0)
包含 [Codex ZIP](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/codebase-llm-wiki-codex.zip)、
[Copilot ZIP](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/codebase-llm-wiki-copilot.zip)、
[update-manifest.json](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/update-manifest.json)
及 [SHA256SUMS](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/SHA256SUMS)。
本機 runtime 驗收仍標示 `runtime-unverified`，CI 通過不代表已完成宿主環境 UAT。

## 由 GitHub Actions 建立 Release

`.github/workflows/release.yml` 是 framework 專用的正式發版流程，只在推送符合
`v*.*.*` 的 tag 時觸發。它以 Python 3.11 與 3.14 矩陣執行 deterministic checks，
再由 Python 3.14 建置兩個平台精簡安裝 ZIP、manifest 與 checksum，最後以
`GITHUB_TOKEN` 建立 GitHub Release。
Installer 不會把這個 framework-only workflow 安裝到 target repository。

1. 更新 `VERSION` 與 `ChangeLog.md`，並確認 LICENSE readiness。
2. 依 [本機驗證手冊](../validation/README.md) 以 Python 3.11 與 3.14 執行完整
   unit、compile、parity、frontmatter、stale、log、stats、lint 與 index checks；
   同一組檢查也會由 tag-triggered workflow 執行。
3. 驗證版本/tag 契約並建置兩個平台資產：

```powershell
python tools/release.py validate --tag v0.3.0
python tools/release.py build --output dist --repository dennis8499/code-base-llm-wiki
```

4. 確認 `dist/` 只包含並正確描述以下資產：

- `dist/codebase-llm-wiki-codex.zip`
- `dist/codebase-llm-wiki-copilot.zip`
- `dist/update-manifest.json`
- `dist/SHA256SUMS`

`bundled_tools` 不是額外的 Release asset；它描述會隨兩個 archive 一起發佈的共用
Skill 工具。此次 bundle 是 Windows x64 tgrep 1.0.5，release builder 會驗證 manifest
中的固定 binary path 與 SHA-256，然後將相同 metadata 寫入 `update-manifest.json`。

5. 提交核准的變更，建立並推送與 `VERSION` 完全相符的 tag：

```powershell
git tag v0.3.0
git push origin v0.3.0
```

6. 將變更合併到 `main` 後推送對應 tag；workflow 會以 `--verify-tag` 明列四個資產，
   並使用 `--generate-notes` 建立 GitHub Release。以下是 workflow 內部的 publish
   step，維護者不需要手動執行：

```yaml
# .github/workflows/release.yml
run: |
  gh release create "${GITHUB_REF_NAME}" \
    dist/codebase-llm-wiki-codex.zip \
    dist/codebase-llm-wiki-copilot.zip \
    dist/update-manifest.json \
    dist/SHA256SUMS \
    --verify-tag \
    --title "Codebase LLM Wiki ${GITHUB_REF_NAME}" \
    --generate-notes
```

不得以 `dist/*` 取代明列資產；這可避免把額外暫存檔誤發佈。完成後從 GitHub
下載四個資產，重新核對 `SHA256SUMS` 與 manifest URL。推送 tag 後的 publish
由 workflow 負責；維護者完成本機檢查、合併及 tag 推送後，仍須確認 workflow
成功並下載正式資產核對 checksum。

每個 ZIP 是一個精簡平台安裝包，包含完整共用 `codebase-wiki` skill、內嵌 installer、
Wiki starter、固定 tgrep bundle、`VERSION`、LICENSE、target `AGENTS.md` 模板，以及
對應的 Codex 或 Copilot adapter。Release builder 會排除框架開發文件、測試、樣例、
框架 Wiki、另一平台入口、generated/cache、
本機 NotebookLM/hook state、transaction journal/lock、stage/backup/temp siblings、
`.env`、credentials/secrets 與 private-key paths。輸出目錄若在 Repo 內，也不會
被重新收入 archive；非排除路徑的 symlink/reparse source 會讓建置失敗。

`.tgrep/` 是 target repo 的使用者管理 generated index/server state，永遠不進入 release
archive；framework 不會自動建立或管理它。共用 Skill 內的 tgrep wrapper、manifest 與
Windows x64 binary 則會隨兩個 ZIP 一起發佈。解壓後仍以 installer 的
`--surface copilot` 或 `--surface codex` 選擇相同平台；若使用錯誤平台包，installer
會在任何 target 寫入前失敗。

## Update manifest

最新 manifest 的穩定網址是：

`https://github.com/dennis8499/code-base-llm-wiki/releases/latest/download/update-manifest.json`

最小契約如下：

```json
{
  "schema_version": 2,
  "product": "codebase-llm-wiki",
  "version": "0.3.0",
  "tag": "v0.3.0",
  "channel": "stable",
  "installer_contract_version": 6,
  "release_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/tag/v0.3.0",
  "bundled_tools": [
    {
      "tool": "tgrep",
      "version": "1.0.5",
      "platform": "windows-x86_64",
      "path": ".agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe",
      "sha256": "9b90e4446e2cbf05e1da086547501e35d7b32f0f6d5f687548cf270b07fbd9d7",
      "source_url": "https://github.com/microsoft/tgrep/releases/tag/v1.0.5"
    }
  ],
  "assets": [
    {
      "name": "codebase-llm-wiki-codex.zip",
      "surface": "codex",
      "format": "zip",
      "download_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/codebase-llm-wiki-codex.zip",
      "sha256": "..."
    },
    {
      "name": "codebase-llm-wiki-copilot.zip",
      "surface": "copilot",
      "format": "zip",
      "download_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/codebase-llm-wiki-copilot.zip",
      "sha256": "..."
    }
  ]
}
```

未來 Extension 應讀取本地 `.agents/skills/codebase-wiki/VERSION`，比較 manifest
的 SemVer，下載對應 asset、驗證 `sha256`，最後呼叫 conflict-safe `upgrade`。
本專案目前只提供 manifest 與版本標記，不自動執行更新。

## 常見錯誤

- 缺少 LICENSE、`VERSION` 不是三段數字，或 tag 不等於 `v` 加上 `VERSION` 時，
  `release.py` 會在建立資產前失敗。
- tgrep manifest、固定版本／平台／路徑或 binary SHA-256 不一致時，`release.py build`
  會在建立 archive 前失敗；這不會自動下載或替換 binary。
- 任一 deterministic check 失敗時不得發版。完整自動檢查通過後可發佈標示
  `static-compatible / runtime-unverified` 的版本；目前 Codex v6 host runtime
  尚未重跑，Release 說明必須保留此限制。
- 只有五項 active Codex UAT 各取得完整 3/3 時，才能宣告相應 host runtime
  `runtime-verified`；歷史 v4 結果不能代替目前版本的驗收。
- `gh release create` 前若 tag 未推送，`--verify-tag` 會拒絕發布。
- 下載後應先驗證 `SHA256SUMS`，再執行 installer。
- `upgrade` 發現目標檔案有人工修改時會回報 conflict，不會覆寫 Wiki 或其他
  使用者內容。

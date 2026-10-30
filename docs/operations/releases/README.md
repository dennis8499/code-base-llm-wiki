# 版本、GitHub Actions 發佈與更新契約

## 版本來源與 readiness gate

產品版號唯一來源是 Repo 根目錄的 `VERSION`，格式為穩定 SemVer
`MAJOR.MINOR.PATCH`；目前版號是 `0.7.0`。Git tag 必須是完全對應的
`vX.Y.Z`。Installer 產生的 `.agents/skills/codebase-wiki/VERSION` 是目標 Repo
的本地版本標記；`contract_version: 7` 則是獨立的 installer/API contract。

本 Repo 採用 MIT License。`tools/release.py validate` 與 `build` 會在建立正式資產前
驗證授權、版本與上游 attribution readiness。不得用參數或修改 fixture 以外的資料
繞過此 gate。

## 歷史發版資產範例：v0.3.0

Codebase LLM Wiki v0.3.0 已於 2026-10-03 發布，來源 tag 指向
[`538712f`](https://github.com/dennis8499/code-base-llm-wiki/commit/538712f553457d53b8e451d1733fe97a01c6aff6)。
已通過 Python 3.11 與 3.14 release checks；[正式 Release](https://github.com/dennis8499/code-base-llm-wiki/releases/tag/v0.3.0)
包含 [Codex ZIP](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/codebase-llm-wiki-codex.zip)、
[Copilot ZIP](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/codebase-llm-wiki-copilot.zip)、
[update-manifest.json](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/update-manifest.json)
及 [SHA256SUMS](https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.3.0/SHA256SUMS)。
v0.7.0 新增固定離線版 Archify v3.2.0 與十類 Wiki 視覺化，並保留 BA/SA/SD 與 Synthesis。GitlabWorkSpace 只為 Group 來源範圍套用覆層。十類圖表 fixture 已通過瀏覽器驗證；Codex/Copilot host UAT 與其他作業系統尚未實測。

## 由 GitHub Actions 建立 Release

`.github/workflows/release.yml` 在 PR、main push、手動與 reusable 呼叫時執行完整
Python 3.11／3.14 deterministic matrix，由 Python 3.14 cell 建置一次兩個平台精簡 ZIP、
manifest 與 checksum。只有版本 tag push 可透過 `GITHUB_TOKEN` 建立正式 GitHub Release。
Tag 優先重用七天內、可信 main push 或 main 手動執行、相同提交與完整矩陣的成功證據；workflow／驗證政策、
環境、來源與產物摘要不符或附件過期時，重跑完整矩陣後才發布，不降低既有 gates。
Publish 下載並驗證證據與四個資產，直接提升同一份位元組，不重新建置。
Actions artifact ZIP API 使用 `application/vnd.github+json`，Release asset 的原始下載才使用
`application/octet-stream`。兩者均驗證完整 CI 證據及 SHA；不以本機建置取代正式產物。
v0.6.3 的 tag 發布因舊標頭得到 HTTP 415，未建立正式 Release；保留原 tag，修正以 v0.6.4 發布。
Installer 不會把這個 framework-only workflow 安裝到 target repository。

1. 更新 `VERSION` 與 `ChangeLog.md`，並確認 LICENSE readiness。
   使用工作台的 release manager 準備下一版時，候選提交須已完成來源分析與 Wiki readiness。
   Manager 只更新 `VERSION` 與 README 的現行版本資訊，再執行：

```text
python tools/prepare_release.py --baseline <candidate-SHA> --version X.Y.Z --format json
```

   Helper 先驗證固定候選提交的完整 Wiki preflight，只重用既有分析，刷新版本 metadata 的
   coverage hash、discovery ID、來源摘要及 append-only log。任何其他來源、README 正文、Wiki
   人工內容或新增檔案都會阻擋，不建立新 disposition，也不代替框架維護。相同輸入重試產生相同
   bytes；已完成部分寫入時僅接受原始或精確預期的產物。Log 日期固定於候選提交與既有紀錄，避免
   跨日重試漂移。Release notes 存在工作台證據目錄，不新增 framework raw-source 檔案。
2. 依 [本機驗證手冊](../validation/README.md) 以 Python 3.11 與 3.14 執行完整
   unit 與 `python tools/validate_release.py --format json`。聚合入口涵蓋 compile、parity、
   frontmatter、stale、log、stats、lint、index 與 scan；PR/main CI 也執行同一組 gates。
3. 驗證版本/tag 契約並建置兩個平台資產：

```powershell
python tools/release.py validate --tag v0.7.0
python tools/release.py build --output dist --repository dennis8499/code-base-llm-wiki
```

4. 確認 `dist/` 只包含並正確描述以下資產：

- `dist/codebase-llm-wiki-codex.zip`
- `dist/codebase-llm-wiki-copilot.zip`
- `dist/update-manifest.json`
- `dist/SHA256SUMS`

`bundled_tools` 不是額外的 Release asset；它描述會隨兩個 archive 一起發佈的共用
Skill 工具。此次 bundle 是 Windows x64 tgrep 1.0.5 + Archify v3.2.0； release builder 會驗證 manifest
中的固定 binary path 與 SHA-256，然後將相同 metadata 寫入 `update-manifest.json`。

5. 提交核准變更並合併至 `main`，再建立並推送與 `VERSION` 完全相符的 tag：

```powershell
git tag v0.7.0
git push origin v0.7.0
```

6. Workflow 的 `scripts/release_ci.py publish` 重新確認版本/tag、固定提交、完整證據與
   SHA-256，驗證已推送 tag、產生 Release notes，並明列四個資產建立 GitHub Release。
   下例顯示首次建立 Release 的等價命令；正常發布由 helper 執行，維護者無須手動執行：

```yaml
# scripts/release_ci.py 首次發布的等價命令
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
下載四個資產，重新核對 `SHA256SUMS` 與 manifest URL。Publish 可重試：既有同名附件必須
內容相同，只補齊缺漏附件；不同內容即停止，不覆寫既有資產。發布完成後重新下載正式附件
核對摘要，並保存 publication 證據。維護者完成本機檢查、合併及 tag 推送後，仍須確認 workflow 成功。

每個 ZIP 是一個精簡平台安裝包，包含完整共用 `codebase-wiki` skill、內嵌 installer、
Wiki starter、固定 tgrep and Archify bundles、`VERSION`、LICENSE、target `AGENTS.md` 模板，以及
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

Archify v3.2.0 is pinned and packaged offline. Install and diagram generation do not download or update it. Node.js 18+ is required. The first runtime acceptance targets Windows; other operating systems are not yet tested. `.gitattributes` marks the vendored files and manifest as `-text` so Git does not normalize their upstream line endings and invalidate pinned hashes on Windows checkouts.

## Update manifest

最新 manifest 的穩定網址是：

`https://github.com/dennis8499/code-base-llm-wiki/releases/latest/download/update-manifest.json`

最小契約如下：

```json
{
  "schema_version": 2,
  "product": "codebase-llm-wiki",
  "version": "0.7.0",
  "tag": "v0.7.0",
  "channel": "stable",
  "installer_contract_version": 7,
  "release_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/tag/v0.7.0",
  "bundled_tools": [
    {
      "tool": "tgrep",
      "version": "1.0.5",
      "platform": "windows-x86_64",
      "path": ".agents/skills/codebase-wiki/bin/windows-x64/tgrep.exe",
      "sha256": "9b90e4446e2cbf05e1da086547501e35d7b32f0f6d5f687548cf270b07fbd9d7",
      "source_url": "https://github.com/microsoft/tgrep/releases/tag/v1.0.5"
    },
    {
      "tool": "archify",
      "version": "3.2.0",
      "platform": "node.js-cross-platform",
      "path": ".agents/skills/codebase-wiki/vendor/archify/bin/archify.mjs",
      "sha256": "3cebcee3fa339e3b98deacae8cb9a5570525e003d8823368d304d904ba9ceecd",
      "source_url": "https://github.com/tt-a1i/archify/releases/tag/v3.2.0",
      "source_commit": "208acba8d412335185b2056fedf54b3405df43fb",
      "archive_sha256": "70e210265c59f24dcbdf2a502ff671104b5454e7ee7d3554aecd86bad32384f5",
      "manifest_path": ".agents/skills/codebase-wiki/vendor/archify-manifest.json",
      "manifest_sha256": "15c1b258d6958b964d4bf41f87e596e79ff5751cb438173c6b4f95bbad519509",
      "license": "MIT",
      "node_requirement": ">=18",
      "file_count": 200
    }
  ],
  "assets": [
    {
      "name": "codebase-llm-wiki-codex.zip",
      "surface": "codex",
      "format": "zip",
      "download_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.7.0/codebase-llm-wiki-codex.zip",
      "sha256": "..."
    },
    {
      "name": "codebase-llm-wiki-copilot.zip",
      "surface": "copilot",
      "format": "zip",
      "download_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.7.0/codebase-llm-wiki-copilot.zip",
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
  `static-compatible / runtime-unverified` 的版本；目前 Codex v7 host runtime
  尚未重跑，Release 說明必須保留此限制。
- 只有五項 active Codex UAT 各取得完整 3/3 時，才能宣告相應 host runtime
  `runtime-verified`；歷史 v4 結果不能代替目前版本的驗收。
- `gh release create` 前若 tag 未推送，`--verify-tag` 會拒絕發布。
- 下載後應先驗證 `SHA256SUMS`，再執行 installer。
- `upgrade` 發現目標檔案有人工修改時會回報 conflict，不會覆寫 Wiki 或其他
  使用者內容。

# 版本、發佈與更新契約

## 版本來源

產品版號唯一來源是 Repo 根目錄的 `VERSION`，格式為穩定 SemVer：
`MAJOR.MINOR.PATCH`，目前初始版號為 `0.1.0`。Git tag 必須使用
`vX.Y.Z`，例如 `VERSION=0.1.0` 對應 `v0.1.0`。

`.agents/skills/codebase-wiki/VERSION` 是 installer 寫入目標 Repo 的本地版本
標記。它由框架的 `VERSION` 產生，不應由使用者手動維護。

`contract_version: 2` 是 installer/API contract 版本，與產品版號獨立，不能
用產品版號取代。

## 建立 Release

發佈前先在目前分支更新 `VERSION` 與 `ChangeLog.md`，再執行：

```powershell
python tools\release.py validate --tag v0.1.0
python tools\release.py build --output dist --repository dennis8499/code-base-llm-wiki
```

確認測試通過後，提交並推送版本 tag：

```powershell
git tag v0.1.0
git push origin v0.1.0
```

`.github/workflows/release.yml` 只接受與 `VERSION` 完全相符的 `vX.Y.Z` tag，
通過 framework checks 後建立 GitHub Release。每個 Release 會附帶：

- `codebase-llm-wiki.zip`
- `codebase-llm-wiki.tar.gz`
- `update-manifest.json`
- `SHA256SUMS`

套件包含完整框架 Repo；安裝時仍使用既有 installer 的 `--surface copilot` 或
`--surface codex` 選擇平台入口。

## Update manifest

最新 manifest 的穩定網址是：

`https://github.com/dennis8499/code-base-llm-wiki/releases/latest/download/update-manifest.json`

其最小契約如下：

```json
{
  "schema_version": 1,
  "product": "codebase-llm-wiki",
  "version": "0.1.0",
  "tag": "v0.1.0",
  "channel": "stable",
  "installer_contract_version": 2,
  "release_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/tag/v0.1.0",
  "assets": [
    {
      "name": "codebase-llm-wiki.zip",
      "format": "zip",
      "download_url": "https://github.com/dennis8499/code-base-llm-wiki/releases/download/v0.1.0/codebase-llm-wiki.zip",
      "sha256": "..."
    }
  ]
}
```

未來 Extension 應讀取本地 `.agents/skills/codebase-wiki/VERSION`，再讀取
manifest 的 `version` 並以 SemVer 比較；版本較新時下載對應 asset、驗證
`sha256`，最後呼叫既有 conflict-safe `upgrade` 流程。本專案目前只提供
manifest 與版本標記，不自動執行 Extension 更新。

## 常見錯誤

- `VERSION` 不是三段數字時，release builder 會拒絕建立資產。
- tag 不是 `v` 加上 `VERSION` 時，GitHub workflow 會在建立 Release 前失敗。
- 下載後應先驗證 `SHA256SUMS`，再執行 installer。
- `upgrade` 發現目標檔案有人工修改時會回報 conflict，不會覆寫 Wiki 或其他
  使用者內容。

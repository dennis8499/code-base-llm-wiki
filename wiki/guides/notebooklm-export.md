---
title: NotebookLM Enterprise — Wiki-first 匯出與增量更新
type: guide
sources:
  - .agents/skills/codebase-wiki/scripts/export-notebooklm.py
  - .agents/skills/codebase-wiki/references/notebooklm-export-workflow.md
  - .agents/skills/codebase-wiki/assets/notebooklm.toml
  - .github/prompts/export-notebooklm.prompt.md
  - Codex.md
  - docs/workflows/README.md
  - docs/setup/README.md
  - README.md
  - .gitignore
  - tools/release.py
last_updated: 2026-08-17
tags: [guide, notebooklm, export, incremental, enterprise]
status: active
---

# NotebookLM Enterprise — Wiki-first 匯出與增量更新

> 將本地 Codebase LLM Wiki 整理成可審查、可手動上傳且可重跑比對的 NotebookLM
> source pack。這是離線產出流程，不是 NotebookLM API 或自動同步服務。

## 適用情境

當維護者希望讓其他使用者透過 NotebookLM 介面了解整個專案時，使用
`/export-notebooklm` 或 Codex 的自然語言 recipe。Exporter 以 Wiki 為主要真相，
只有 Wiki page `frontmatter.sources` 宣告的 evidence（以及明確設定的額外 paths）
才會納入；不會無條件複製整個 raw source tree。

## 執行前檢查

1. 閱讀 `wiki/index.md` 與全部 Wiki pages，排除 `wiki/log.md`。
2. 執行 frontmatter、stale-source 與 lint checks。
3. 若有 `stale`、`placeholder`、缺口或矛盾，先回報 bounded Ingest 範圍；確認後才更新 Wiki、同步 index 並追加合法 log entry。
4. 確認 Wiki pages 與 evidence 的 scope 不包含 credentials、secrets、generated artifacts 或不應分享的內容。

## 產生 source pack

```powershell
python .agents\skills\codebase-wiki\scripts\export-notebooklm.py `
  --root . --output .notebooklm --format json
```

可把 `.agents/skills/codebase-wiki/assets/notebooklm.toml` 複製成 Repo root 的
`notebooklm.toml` 以調整 `source_limit`、`reserved_source_slots`、
`max_source_bytes`、`max_source_words`、`include_evidence`、`extra_paths` 或
`exclude_paths`。設定只能降低硬限制，路徑必須是 Repo-relative。

輸出目錄包含：

- `sources/*.md`：唯一應手動加入 NotebookLM 的 source files；
- `manifest.json`：schema、profile、設定 limits、input/output hashes、stable IDs、warnings 與 skipped paths；
- `upload-plan.md`：本次相對上一次 manifest 的操作分類；
- `README.md`：給上傳者的本機操作摘要。

## 穩定識別與更新

每個 source 有 stable `logical_source_id`：`project-map`、`wiki:<path>`、
`evidence:<parent-directory>`；超大 source 會以 `#part-###` suffix 拆分。重跑
exporter 後依 `upload-plan.md` 操作：

| 狀態 | NotebookLM 手動操作 |
| --- | --- |
| `added` | 上傳新 Markdown source |
| `changed` | 先移除舊 static source，再上傳新檔 |
| `deleted` | 移除 NotebookLM 中的舊 source |
| `unchanged` | 不需重新上傳 |

不要把 `manifest.json`、`upload-plan.md` 或 README 當成專案 evidence 上傳。
Exporter 會保留 output directory 中不由它管理的檔案；Git 預設忽略整個
`.notebooklm/`，release builder 也不會把它打包。

## 容量與安全

Enterprise profile 的 hard limits 是每本 notebook 最多 300 sources、每個 source
最多 500 MB 與 500,000 words。Exporter 預設使用較低的 450 MB 與 450,000
estimated words safety limits，並可預留 source slots；超過可用 source 數量或無法
安全切分時，會在 commit 前失敗並保留舊 pack。不同 Workspace tier 的 source limit
請在 `notebooklm.toml` 下調，不要把較寬的 Enterprise 設定當成所有租戶通用。

預設會回報並排除 secrets/credentials、binary、generated/build/cache、dependency、
framework adapter 目錄與 export output。任何 skipped、warning 或 unresolved item
都必須在交付報告中列出；人工審查仍負責確認商業機密、個資與租戶政策。

## 相關頁面與官方限制

- [[overview]] — 框架三層模型與離線 delivery pack 邊界
- [[framework-introduction]] — 安裝、Wiki-first 工作流與 deterministic checks
- [[release-and-update]] — release 排除本機 pack
- Enterprise 上限與產品行為請以 [Google Cloud Gemini Notebook Enterprise 文件](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview?authuser=2) 為準；Workspace tier 的 source 限制可能不同，參考 [NotebookLM 說明](https://support.google.com/notebooklm/answer/16337734?hl=zh-Hant)。
- 靜態檔案、Google Drive 與同步行為請參考 [NotebookLM source types and sync](https://support.google.com/notebooklm/answer/16215270?co=GENIE.Platform%3DDesktop&hl=en)；本框架選擇離線 static Markdown replacement。

## 未解決事項

- 本流程不包含 NotebookLM API、Drive 自動同步、權限配置或自動刪除 NotebookLM source；使用者仍需在企業版介面手動執行 upload plan。
- 實際可用 source 數量與 Workspace/Enterprise 租戶政策可能變動；執行前應確認管理員設定與官方文件。

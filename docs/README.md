# Codebase LLM Wiki 文件導覽

這是框架 Repo 的文件入口。若第一次接觸專案，先閱讀根目錄的
[README.md](../README.md)；需要了解 Codex 的操作方式，再閱讀
[Codex.md](../Codex.md)。

## 建議閱讀順序

1. [架構與資料流](product/architecture/README.md)：先理解共用 Skill、Copilot/Codex adapters、Hooks、Installer 與 Wiki 的關係。
2. [工作流手冊](product/workflows/README.md)：了解 Ingest、Query、Lint、ADR、Synthesis、標準對齊 BA／SA／SD 與 NotebookLM export。
3. [安裝與升級](operations/setup/README.md)：確認前置需求、平台 surface、guard mode 與升級行為。
4. [驗證手冊](operations/validation/README.md)：執行單元測試、parity、Wiki quality checks 與 E2E 樣例驗收。
5. [版本、發佈與更新契約](operations/releases/README.md)：管理 `VERSION`、GitHub Release、checksums 與 update manifest。
6. [產品變更摘要](history/changes/)：閱讀 Codebase LLM Wiki 的已交付產品變更，不保留 AI SDLC 工作流 records。

## 文件分類

| 位置 | 用途 | 入口 |
| --- | --- | --- |
| `docs/product/architecture/` | 元件、資料流、安全邊界與 installer 架構 | [架構文件](product/architecture/README.md) |
| `docs/product/workflows/` | 使用者意圖、授權規則與各工作流契約 | [工作流手冊](product/workflows/README.md) |
| `docs/operations/setup/` | 安裝、升級、平台啟用與排錯 | [安裝手冊](operations/setup/README.md) |
| `docs/operations/validation/` | 本機 deterministic checks、E2E 驗收與 NotebookLM UAT | [驗證手冊](operations/validation/README.md) |
| `docs/operations/releases/` | 版本、發布資產與更新 manifest | [發布契約](operations/releases/README.md) |
| `docs/history/` | 上游概念 attribution 與歷史材料 | [歷史文件](history/README.md) |
| `docs/history/changes/` | Codebase LLM Wiki 產品變更摘要 | [變更摘要](history/changes/) |
| `samples/` | 不會隨 installer 發布的可操作 E2E 樣例 | [樣例說明](../samples/README.md) |
| `tests/` | 依責任分組的 contract、installer、NotebookLM、release、sample 與 Wiki tests | [測試目錄](../tests/README.md) |

## 專案邊界

這個 Repo 是框架本身，不是要被安裝成第三方 Python 套件的應用程式。
唯一共用執行 Skill 位於 `.agents/skills/codebase-wiki/`，平台 adapter 位於
`.github/` 與 `.codex/`；`docs/`、`samples/`、`tests/` 與框架自己的
`wiki/` 是維護與驗證內容，不屬於 installer surface。

文件只描述目前已由程式、設定、測試或 Wiki 證據支持的行為。專案目前尚未宣告
LICENSE，因此公開 release readiness gate 仍會阻擋發布資產。

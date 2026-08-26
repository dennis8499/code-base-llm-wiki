# Codebase LLM Wiki 文件導覽

這是框架 Repo 的文件入口。若第一次接觸專案，先閱讀根目錄的
[README.md](../README.md)；需要了解 Codex 的操作方式，再閱讀
[Codex.md](../Codex.md)。

## 建議閱讀順序

1. [安裝與升級](setup/README.md)：確認前置需求、平台 surface、guard mode 與升級行為。
2. [工作流手冊](workflows/README.md)：了解 Ingest、Query、Lint、ADR、Guide、Synthesis、SA 與 NotebookLM export。
3. [架構與資料流](architecture/README.md)：理解共用 Skill、Copilot/Codex adapters、Hooks、Installer 與 Wiki 的關係。
4. [驗證手冊](validation/README.md)：執行單元測試、parity、Wiki quality checks 與 E2E 樣例驗收。
5. [版本、發佈與更新契約](releases/README.md)：管理 `VERSION`、GitHub Release、checksums 與 update manifest。

## 文件分類

| 位置 | 用途 | 入口 |
| --- | --- | --- |
| `docs/architecture/` | 元件、資料流、安全邊界與 installer 架構 | [架構文件](architecture/README.md) |
| `docs/setup/` | 安裝、升級、平台啟用與排錯 | [安裝手冊](setup/README.md) |
| `docs/workflows/` | 使用者意圖、授權規則與各工作流契約 | [工作流手冊](workflows/README.md) |
| `docs/validation/` | 自動化檢查、E2E 驗收與 NotebookLM UAT | [驗證手冊](validation/README.md) |
| `docs/releases/` | 版本、發布資產與更新 manifest | [發布契約](releases/README.md) |
| `docs/history/` | 上游概念 attribution 與歷史材料 | [歷史文件](history/README.md) |
| `samples/` | 不會隨 installer 發布的可操作 E2E 樣例 | [樣例說明](../samples/README.md) |
| `tests/` | Installer、contract、guard、release 與 Wiki regression tests | [測試目錄](../tests/) |

## 專案邊界

這個 Repo 是框架本身，不是要被安裝成第三方 Python 套件的應用程式。
共用執行規格位於 `.agents/skills/codebase-wiki/`，平台 adapter 位於
`.github/` 與 `.codex/`；`docs/`、`samples/`、`tests/` 與框架自己的
`wiki/` 是維護與驗證內容，不屬於 installer surface。

文件只描述目前已由程式、設定、測試或 Wiki 證據支持的行為。專案目前尚未宣告
LICENSE，因此公開 release readiness gate 仍會阻擋發布資產。

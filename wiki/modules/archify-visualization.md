---
title: "Archify 互動視覺化"
type: module
summary: "以固定版本 Archify 產生可編輯 JSON、來源對照與可驗證的 Wiki HTML 圖表。"
notebooklm_group: architecture
notebooklm_role: traceability
sources:
  - ".agents/skills/codebase-wiki/capabilities.json"
  - ".agents/skills/codebase-wiki/scripts/wiki-visualize.py"
  - ".agents/skills/codebase-wiki/references/visualization-workflow.md"
  - ".agents/skills/codebase-wiki/vendor/archify-manifest.json"
  - ".agents/skills/codebase-wiki/scripts/install-framework.py"
source_digest: sha256:ea5b265a6ee2006a3d440fdff81947ae9f7980bf5212f68ad7d120b84ce8a5a1
derived_from: ["[[system-architecture]]", "[[installer-and-upgrade]]", "[[platform-adapters-and-release]]"]
last_updated: 2026-10-30
tags: [module, visualization, archify, provenance]
status: active
---

# Archify 互動視覺化

## 用途與授權

只有使用者明確要求繪製或產生圖表時，才進入 `visualize` 工作流。該請求授權建立一份有來源追溯的 HTML 圖表與伴隨 Synthesis 頁；一般 Query 仍唯讀。圖表用來呈現 Wiki 與目前來源的證據，不會補造缺漏的節點、關係或條件。

## 固定套件與圖型

框架隨附正式版 Archify v3.2.0，來源 commit `208acba8d412335185b2056fedf54b3405df43fb`，官方 ZIP SHA-256 為 `70e210265c59f24dcbdf2a502ff671104b5454e7ee7d3554aecd86bad32384f5`。完整套件與 MIT 授權保存在 `.agents/skills/codebase-wiki/vendor/archify/`；逐檔雜湊列於 `.agents/skills/codebase-wiki/vendor/archify-manifest.json`。安裝和執行時都不安裝 Node 套件、不連線下載或自動更新 Archify；執行環境須有 Node.js 18 以上版本。

目前涵蓋 Architecture、Workflow、Sequence、Dataflow、Lifecycle、ERD、Class、Tree、Timeline 與 Waterfall。Agent 讀取對應 schema、作者指引及範例，產生原生 JSON IR；既有 Mermaid 只作內容參考，不會自動解析。預設介面語言為 `zh-TW`、品質為 `showcase`、動畫停用。

## 證據與 Gap

先讀 `wiki/index.md` 和相關 Wiki 頁面；Wiki 缺漏、過時或矛盾時，再讀必要的目前程式與設定。`prepare` 記錄選定頁面和來源的 SHA-256 與完整 Wiki 快照。`evidence-map.json` 逐一對照每個圖表元素的證據路徑和雜湊；沒有證據的元素必須記成 Gap。Git 歷史只可使用既有 bounded offline helper，不執行目標程式、不連線資料庫。

Timeline 的日期和 Waterfall 的耗時必須有來源依據；只有使用者明確要求示意時，才可用標示清楚的示意值。工作樹來源以當下檔案雜湊記錄，不會標示為已提交 commit 的證據。

## 驗證與發布交易

`publish` 在作業系統暫存目錄執行原生 `finalize`；validate、deliver、strict check 與 browser-check 四關全部通過後才進入 Wiki 寫入。每張圖最長 180 秒、子程序總輸出最多 8 MiB；更新檢查及網路使用停用。缺少 Node.js／瀏覽器、JSON 無效、驗證失敗、來源漂移或 Wiki 快照衝突時，都不提交本次產物、索引或日誌。

成功產物放在不可覆寫的 `wiki/visualizations/<slug>/<run-uuid>/`，包含候選 JSON、HTML、manifest、證據映射及原始 receipts。Archify 原生 receipts 保留原執行的絕對暫存路徑；`codebase-wiki-visualization/v1` manifest 記錄版本、輸入／產物雜湊、證據快照及四個驗證結果，讓 `verify` 能檢查搬入 Wiki 後的檔案。

穩定入口為 `wiki/synthesis/diagram-<slug>.md`，保留歷次 UUID 產物與人工 notes，列出來源、Gap 和驗證狀態，並標記 `notebooklm_role: exclude`。產物、伴隨頁、`wiki/index.md` 及單筆 `synthesis` 日誌透過既有 writer/CAS 一次提交；不自動清除舊版本。

## 平台狀態

Codex 使用 `$codebase-wiki` 的自然語言 recipe；Copilot 提供 `/visualize-wiki`。Windows 上 Node.js 與瀏覽器的十類 fixture 都完成四項自動驗證。Codex／Copilot host runtime UAT 尚未執行；macOS 與 Linux 也尚未實測。

## 相關頁面

- [[system-architecture]]
- [[installer-and-upgrade]]
- [[platform-adapters-and-release]]

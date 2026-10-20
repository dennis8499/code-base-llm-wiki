---
title: 資源限制與 Wiki 提交
type: module
summary: 以 bounded offline evidence、單輪快照及單一 writer/CAS 保護來源完整性、資源與人工 Wiki 內容
notebooklm_group: local-runtime-governance
notebooklm_role: exclude
sources:
  - .agents/skills/codebase-wiki/scripts/bounded_process.py
  - .agents/skills/codebase-wiki/scripts/offline_git.py
  - .agents/skills/codebase-wiki/scripts/wiki_transaction.py
  - .agents/skills/codebase-wiki/scripts/wiki-write.py
  - .agents/skills/codebase-wiki/scripts/project_scanner.py
  - .agents/skills/codebase-wiki/scripts/notebooklm_exporter.py
  - .agents/skills/codebase-wiki/scripts/tgrep-search.py
  - tests/wiki/test_resource_bounds.py
  - tests/wiki/test_wiki_transaction.py
  - tests/notebooklm/test_preflight_snapshot.py
  - tools/benchmark_resources.py
  - docs/operations/validation/resource-benchmark.json
source_digest: sha256:7499a6f669ace15a494f878b517ccd0aac3b47dcb22a8b159754f32ab32518fd
derived_from: ["[[system-architecture]]", "[[wiki-quality-and-provenance]]"]
last_updated: 2026-10-21
tags: [module, resource, concurrency, offline, provenance]
status: active
---

# 資源限制與 Wiki 提交

## 已實作的邊界

- Git 證據只允許本機 read commands，強制 `GIT_NO_LAZY_FETCH=1`、`GIT_ALLOW_PROTOCOL=""`、停用互動提示、fsmonitor 及 external diff/textconv。預設 30 秒／8 MiB；缺物件及超限回報缺口。
- Subprocess 並行讀取 stdout／stderr，限制共同 bytes，逾時或超量停止程序樹。Windows 使用 kill-on-close Job Object，POSIX 使用獨立 process group；失敗不交付截斷輸出作成功證據。
- Scanner 仍列舉 ignored、untracked、巢狀 Repo 與自有 automation。Dictionary 加速去重／exact ledger，排除目錄只看 4096 entries 加一筆 lookahead；不讀被排除內容。
- 來源從 8 KiB 起讀，完整 chunk 才倍增至最多 1 MiB；尾端使用小額 EOF probe，單輪 hash／UTF-8 decode 不重開檔。單檔／整輪預設 64／256 MiB；整輪計入 binary、無效 UTF-8、單檔超限與 I/O 失敗前已讀 bytes，不使用有隱藏 read-ahead 的 buffered stream。耗盡後繼續 discovery，但不再開啟後續來源並留下 total-budget gap。恰好用滿額度只在當下 regular-file position／size 證明 EOF 時接受；無法證明則保留 blocked。NotebookLM 同輪共用 source text／SHA、Wiki text／frontmatter，最終 apply 保留完整 discovery、Wiki 與設定漂移檢查。
- `wiki-write.py` 以全 Wiki snapshot、OS lock 及 compare-and-swap 提交頁面、index 與一筆 log。既有日誌正文保持原 bytes，僅更新 frontmatter date 並追加操作。Staging／journal 支援失敗與中斷恢復；crash 後的新人工修改會阻擋恢復。
- `rebuild-index.py --stdout` 只渲染；預設寫入也透過 writer 並記錄 update。其他 Shell／編輯器寫入必須遵守共同流程；helper 不承諾未上鎖讀者的隔離。

## 檢查與結果

`tests/wiki/test_resource_bounds.py` 覆蓋本機 promisor 缺 blob 無 fetch、時間／輸出限制、真正 bounded 目錄列舉、UTF-8 chunk 邊界、短讀取、微小檔案與大檔尾端配置，以及連續 invalid／binary／oversized 來源的實際累計 read bytes、額度耗盡後零開檔、EOF／成長衝突與 I/O 失敗計費。`tests/notebooklm/test_preflight_snapshot.py` 核對單次來源讀取、plan 重用及 source／Wiki／config 在 apply 中漂移時保留舊 pack。`tests/wiki/test_wiki_transaction.py` 覆蓋 CAS、writer lock、失敗 rollback、crash recovery、人工修改衝突及輸入邊界。

`tools/benchmark_resources.py` 的歷史 scanner 測量使用 in-memory file doubles，未包含實體磁碟 I/O；Windows Python 3.14.7 三次中位數 8,000 files 為 3.988 → 1.655 秒。Log 則使用實體暫存頁面，201 pages／1,000 links 為 3.084 → 0.0267 秒。後續實體 8,000 個 10-byte 檔案曾暴露舊候選串流配置退步；保留該失敗實測後修正起讀大小。另以五組交替、各自 fresh process 的修正前後微測，舊候選 5.991 秒 → 修正後 1.195 秒，每輪 snapshot、1,512,963-byte inventory 與 8,000 次來源開檔完全一致，原始 rows 與實作 SHA 存於 `docs/operations/validation/resource-benchmark.json`。這些是本機局部測量；正式 HEAD 配對、端到端與服務容量各自驗收。

## 使用

依 Skill 的 `references/resource-safety.md` 執行 bounded Git、設定 scan budgets，以及準備完整 snapshot／writes／deletes／log_append 的 Wiki 交易。框架程式及單元回歸是本機證據，Codex／Copilot 對話、服務容量及租戶驗收仍依 [[business-knowledge-gaps]] 保留限制。

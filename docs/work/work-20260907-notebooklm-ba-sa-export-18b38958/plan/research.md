# 規劃證據

查核日期：2026-09-07。此文件保存本次唯讀查證的摘要及原始來源定位；不表示實作已完成。

## Observed：專案與 runtime

- Python availability probe：`python --version` 回傳 Python 3.14.6；`import unittest` 成功，來自 Python 標準函式庫。
- 以 `unittest.defaultTestLoader.discover('tests').countTestCases()` 唯讀探索現有 suite，取得 175 tests；未執行測試，沒有通過率聲明。
- Path existence probe：`tests/notebooklm_acceptance.py`、`tests/test_notebooklm_acceptance.py`、`tests/test_notebooklm_contract.py` 均不存在。新 runner 與 commands 為 Proposed。
- `.github/workflows/` 沒有可沿用的產品 CI；`docs/validation/README.md` 要求本機 deterministic checks。本次不新增 CI 或部署流程。
- 現有 `export-notebooklm.py` 可載入 `notebooklm_exporter.main`，已有 public CLI seam；BOOT 不適用。
- `notebooklm_exporter.py:1257` 的 safe scan 收集 path/category/byte_count/sha256；`:1618` 的 coverage 只驗證 BA 結構，`:3548` 組合 readiness，`:3865` 的 main 驗證 preflight ID 後 apply。
- `.agents/skills/codebase-wiki/capabilities.json` 宣告 discovery_plan 與 readiness_apply 兩個確認階段；此要求由本次 Ready 需求 FR-003 明確變更。
- `.agents/skills/codebase-wiki/references/system-analysis-workflow.md` 的 standalone SA 是 solution-neutral 且 traceability-only；本次新增 export 專用現況 profile，不將所有技術追溯頁直接變成上傳候選。

## 官方來源摘要

- Python 3.11 unittest：https://docs.python.org/3.11/library/unittest.html 。TestCase、fixture、TestLoader、TestResult 與獨立 test selection 均為標準函式庫能力。現有 repo 已使用 unittest；本次沿用它承載 Given/When/Then 行為案例，不增加第三方 BDD dependency。Python 3.11 的最低版本能力有文件依據，本機 availability 只證明 3.14.6。
- Google 產品概覽：https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview ，更新日期 2026-08-26。單一 Notebook 為 300 sources；每來源 500 MB 或 500,000 words；Markdown 可作為來源，上傳建立靜態副本。分享限同一 Cloud project，控制項包含 IAM、VPC-SC、CMEK 及資料位置。
- Google 內容防護：https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/protect-sensitive-data ，更新日期 2026-08-31。Sensitive Data Protection 檢查來源，Model Armor 檢查互動；大型檔案另有掃描限制，不能以容量合格推定已受保護。本次保留官方連結與查核日期，管理員負責確認租戶設定，沒有雲端 API 呼叫。

## 選項與決策證據

- TD-001：export 專用 as-is BA/SA profiles 比全域改寫 standalone BA/SA 語義更符合此次 export 範圍；兩份功能文件保留，upload sources 另行編排以避免 300-source 上限衝突。
- TD-002：只保留一次人類確認；來源 discovery ID 排除 Wiki，readiness ID 仍綁 final Wiki。相較取消全部 ID 檢查，本方案保留 source/config drift 拒絕。
- TD-003：沿用 deterministic packing、DLP 與 transaction；相較新增 NotebookLM API，本方案符合離線本機交付邊界。

## 人工語意驗證

QA 維護者在隔離 Task Tracker fixture 驗證 BA/SA：逐項以 code 路徑與 locator 核對事實；故意與 code 衝突的 README 必須被標示，缺少的目標與政策必須維持「Codebase 未提供證據」。核對來源讀取紀錄、所有功能配對、繁中敘述與人工 notes 保留，逐列 pass/fail；失敗不得宣告萃取完整。NotebookLM 租戶回答品質與雲端控制只列未驗證，無 tenant 實測不得聲稱通過。

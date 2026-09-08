# 2026-09-07：NotebookLM 現況 BA／SA 匯出

這是 Codebase LLM Wiki 的產品變更摘要；原始 AI SDLC planning、handoff 與 outcome
records 已移除，產品契約以共用 Skill、測試、文件與 Wiki 為準。

## 變更

- NotebookLM exporter 升級為 schema v6，從當下完整安全 Codebase 建立 discovery。
- 預覽只需一次使用者確認；之後產生每功能互連的 current-state BA／SA、query index、
  project map、shared business context 與 upload plan。
- `discovery_id` 綁定 raw inventory；`preflight_id` 綁定 Wiki、coverage、DLP 與 pack
  readiness，apply 以雙識別碼與原子輸出保護上一份有效 pack。
- raw source 保持唯讀；Wiki 是持久知識層；敏感資料遮罩、容量限制與 Google tenant
  controls 分開報告，不宣稱雲端驗證已完成。

## 產品證據

- `.agents/skills/codebase-wiki/scripts/notebooklm_exporter.py`
- `.agents/skills/codebase-wiki/references/notebooklm-export-workflow.md`
- `.github/prompts/export-notebooklm.prompt.md`
- `tests/notebooklm/`
- `docs/operations/validation/notebooklm-ba-uat.md`

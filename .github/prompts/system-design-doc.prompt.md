---
name: system-design-doc
description: >
  基於 Codebase LLM Wiki 產生 ISO/IEC/IEEE 42010 對齊的 SD 系統設計文件與可追溯 views。
agent: "wiki-keeper"
argument-hint: "可選：範圍，例如：整體系統、認證子系統、匯出流程"
---

## 任務

產出一份繁中 Markdown System Design 文件。

**設計範圍**：${input:scopeName:整體系統}

## 流程

1. 完整載入 `.agents/skills/codebase-wiki/references/system-design-workflow.md`、
   `.agents/skills/codebase-wiki/references/analysis-document-standards.md` 與
   `.agents/skills/codebase-wiki/assets/system-design-template.md`。
2. 讀取 `wiki/index.md`、近期 `wiki/log.md`、對應 SA／BA、architecture、
   decisions、modules、entities、dependencies 與 gaps；缺少 SA 時建立具體 Gap。
3. 建立 stakeholder/concern、viewpoint/view、design element 與 coverage inventories；
   使用 `DE-{SCOPE}-NNN`、`VIEW-{SCOPE}-{SLUG}` 並重用既有 ADR。
4. Wiki 不足、stale 或矛盾時才唯讀回溯 raw sources；區分 approved decision、
   implementation observation、inference 與 Gap。
5. 元件、runtime、資料、部署與安全 Mermaid 各自需要證據；不足時保留槽位並寫 Gap。
6. 整體系統寫入 `wiki/synthesis/system-design.md`；指定範圍寫入
   `wiki/synthesis/{kebab-scope}-system-design.md`。
7. 只重建 managed block，保留 user-notes，詳細 paths／symbols 放 local-only。
8. 更新 `wiki/index.md`，並在 `wiki/log.md` 追加一筆 `synthesis` 記錄。

## 品質要求

- Frontmatter 必須有 `standards_profile: system-design-aligned-v1`、
  `coverage_status` 與 `notebooklm_role: traceability`。
- `sources` 只列真實 repo-relative raw source 路徑；Wiki 證據放 `derived_from`；
  無 raw evidence 時使用 `sources: []`。
- 不得編造 component、protocol、schema、topology、trust boundary、quality tactic
  或 architecture decision；證據不足仍產出文件並登錄 Gap。
- 完成前執行 frontmatter、stale、index、log 與 lint 檢查。

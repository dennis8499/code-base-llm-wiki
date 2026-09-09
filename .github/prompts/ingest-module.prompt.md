---
name: ingest-module
description: >
  互動式攝入單一模組到 wiki——讀取指定模組的原始碼，
  摘要討論後寫入結構化 wiki 頁面。
agent: "agent"
argument-hint: "模組路徑，例如：src/auth 或 app/services/user"
---

對 `${input:modulePath}` 執行 **Interactive Ingest**。

完整載入並遵守 [Ingest workflow](../../.agents/skills/codebase-wiki/references/ingest-workflow.md)。
需要定位大量 import/export 或 symbol 時，依 [Source Discovery with tgrep](../../.agents/skills/codebase-wiki/references/source-discovery-workflow.md)
使用共用唯讀 wrapper；搜尋結果只作 locator，必須重新讀取目前 source。
先探索並摘要職責、公開介面、相依性、特殊分支與風險，然後**等待確認**；
確認前不得寫檔。確認後只修改授權的 Wiki surface，並完成 frontmatter、
`source_digest`、wikilinks、`wiki/index.md` 與單一 `wiki/log.md` ingest entry。

Raw sources 全程唯讀。只有 workflow completion criterion 全部成立才回報完成。

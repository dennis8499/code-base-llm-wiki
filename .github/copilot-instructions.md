# Copilot Instructions — Codebase LLM Wiki

Copilot 與 Codex 共用 `.agents/skills/codebase-wiki/`；它是 intent、
workflow、schema、template 與 hook logic 的共同來源。

## 模型

| Layer | Wiki task policy |
| --- | --- |
| Raw source code、config、既有文件、Git history | Read-only |
| `wiki/` | 經授權的持久 Wiki 產出 |
| Framework schema/docs/tests | 僅 framework maintenance |

使用 `.agents/skills/codebase-wiki/SKILL.md` 路由，並在行動前完整載入
`references/intent-routing.md` 選出的 workflow reference。

## 不變量

- Wiki-first：index、相關頁面、最後才是 evidence gap 的 sources。
- Evidence-first：標示 inference、speculation 與 gap。
- `frontmatter.sources` 使用真實 repo-relative paths 或 `sources: []`。
- Wiki links 使用 `[[page-name]]`；source paths 使用反引號。
- 保留人工內容，`wiki/log.md` 維持 append-only。
- page add/delete/rename/major update 同步 `wiki/index.md`。
- Lint 先報告 findings，再確認 repairs。
- Custom agents 是 explicit-delegation only；一般任務由目前 agent 完成。

## Copilot Adapter

- Prompts：`.github/prompts/`
- Explicit-delegation agents：`.github/agents/`
- Hook configuration：`.github/hooks/`
- Canonical hook logic：`.agents/skills/codebase-wiki/scripts/hooks/`
- Page schema/template selection：`.agents/skills/codebase-wiki/references/`

只有 workflow completion criterion、deterministic checks、index coupling 與
append-only log coupling 全部完成後，才回報 durable task 完成。

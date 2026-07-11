# Wiki Log Operations

Use this file as the source of truth for the `{operation}` field in
`wiki/log.md` entries.

## Format

```markdown
## [YYYY-MM-DD] {operation} | {subject}

- Change summary
- Affected pages: [[page-a]], [[page-b]]
```

`wiki/log.md` is append-only. Do not delete or rewrite existing entries.

## Allowed Operations

| Operation | Use when |
| --- | --- |
| `ingest` | Raw source evidence was read and wiki pages were created or updated. |
| `query` | A query result was saved or materially changed wiki knowledge. Pure chat answers do not need a log entry. |
| `lint` | Wiki health checks or accepted lint repairs changed wiki state. |
| `update` | Schema, index, hooks, documentation, or framework maintenance changed durable repo behavior. |
| `init` | Initial wiki skeleton or first-time framework setup was created. |
| `adr` | An Architecture Decision Record was created or materially updated. |
| `synthesis` | Durable cross-cutting analysis or a system analysis document was saved under `wiki/synthesis/`. |
| `guide` | Durable operational, onboarding, debugging, or contributor guidance was saved under `wiki/guides/`. |
| `archaeology` | Git history or legacy behavior findings were persisted to wiki pages. |

## Operation Selection

- Use `synthesis` for SA documents because SA output lives under
  `wiki/synthesis/`.
- Use `query` only when a query result is persisted; normal read-only query
  answers do not modify `wiki/log.md`.
- Use `update` for framework schema maintenance that changes instructions,
  hooks, scripts, prompts, or documentation without changing wiki content pages.

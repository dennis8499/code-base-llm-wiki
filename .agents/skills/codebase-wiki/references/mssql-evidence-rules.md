# SQL Server Live Evidence Rules

Use SQL Server / MSSQL tools only when the current environment actually exposes
them and the user's question needs live database evidence.

## Allowed Operations

- Connection metadata and connection details.
- Listing servers, databases, schemas, tables, views, and functions.
- Schema discovery and metadata lookup.
- Bounded read-only `SELECT` queries with an explicit limit or narrow predicate.

## Forbidden Operations

- DML: `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`.
- DDL: `CREATE`, `ALTER`, `DROP`.
- `EXEC` or stored procedure execution.
- Unbounded table scans.
- Credential disclosure.
- Any operation that changes persistent database state.

## Required Evidence Metadata

Every DB-derived answer must include:

- `connected_at`
- `source_tool`
- `server`
- `database`
- `query_scope`
- `result_limit`
- `row_count`
- `freshness_note`

## Persistence Rules

- DB evidence is not a repo file and must not be placed in
  `frontmatter.sources`.
- If DB evidence is persisted after user confirmation, keep it in a page body
  evidence block with the metadata above.
- If no SQL Server / MSSQL tool is available, state that clearly and ask before
  using GitHub Copilot, MCP, CLI, or another fallback path.

## Completion Criterion

Live evidence is complete when the query is bounded and read-only, all required
metadata fields are present, freshness limitations are stated, credentials are
absent, and any persisted evidence appears only in a Wiki page body.

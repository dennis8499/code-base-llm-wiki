# LLM Wiki — upstream concept note

This project was inspired by Andrej Karpathy's “LLM Wiki” concept:

- Original source: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Upstream author: Andrej Karpathy
- Accessed for this implementation: 2026-08-21

The upstream document describes a persistent, interlinked Markdown knowledge
layer maintained by an LLM between immutable raw sources and the instructions
that govern ingestion, querying, linting, indexing, and change logging. The key
idea is that knowledge compounds in durable pages instead of being reconstructed
from retrieved chunks for every question.

Codebase LLM Wiki is an independent implementation of that pattern for software
repositories. Its installer, schema, hooks, safety boundaries, provenance model,
NotebookLM export, tests, and platform adapters are project-specific work.

The full upstream text is intentionally not mirrored here because the referenced
Gist does not declare a redistribution license. Consult the source link for the
authoritative wording and history.

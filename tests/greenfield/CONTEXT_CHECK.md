# Fresh-project context check

This fixture represents a newly scaffolded strict Next.js 15 App Router project before feature work. `tests/validate_template.py` copies it to a new temporary directory, pastes the canonical `CLAUDE.md` without modification, and checks the resulting project contract.

Replay prompt for Claude Code from the temporary project root:

> Without changing files, identify the stack and runtime, then name where a projects migration, SQL query, input schema, business rule, and HTTP handler belong. List the existing validation commands you may run. If the repository provides enough context, finish with `NO_CLARIFICATION_NEEDED`; otherwise ask one question.

The repository provides deterministic answers: Next.js 15 App Router, strict TypeScript, Node.js SQLite through `better-sqlite3`, and the migration/query/validation/service/route paths exercised by this fixture. The replay is intentionally read-only so a reviewer can run it with Claude Code without accepting generated edits.

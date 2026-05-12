# Next.js 15 + SQLite CLAUDE.md Template

An opinionated `CLAUDE.md` for a greenfield SaaS using Next.js 15 App Router and SQLite through `better-sqlite3` or Turso/libSQL.

## Use It

1. Create a new Next.js 15 App Router project.
2. Copy `templates/nextjs-sqlite/CLAUDE.md` into the project root.
3. Start Claude Code from the project root and ask it to implement a small SaaS feature.

## Validation

```bash
python3 tests/validate_nextjs_sqlite_claude.py
```

The validation checks for the required sections, concrete commands, migration rules, anti-patterns with reasons, and Next.js + SQLite specificity.

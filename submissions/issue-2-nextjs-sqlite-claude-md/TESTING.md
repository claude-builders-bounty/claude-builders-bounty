# Testing

## Local Validation

```bash
python3 submissions/issue-2-nextjs-sqlite-claude-md/tests.py
```

Result:

```text
tests_ok=true
```

The test copies `CLAUDE.md` into a temporary greenfield Next.js + SQLite SaaS fixture and checks that the file covers stack, structure, naming, migration rules, commands, component patterns, and anti-patterns.

## Context Check

The included `samples/context-check.md` shows the no-clarifying-question behavior expected when an agent reads this `CLAUDE.md` before implementing a typical SaaS feature.

# Validation

Manual validation target for this template:

1. Create a fresh Next.js 15 App Router project
2. Add SQLite usage via `better-sqlite3`
3. Paste `CLAUDE.md` at the repo root
4. Ask Claude Code to:
   - explain the expected folder structure
   - suggest where migrations should live
   - name the command it would run for tests and typecheck
   - explain whether it should default to server or client components

Expected outcome:

- Claude answers without asking clarifying questions about the core stack
- Claude recommends the same conventions described in the template
- Claude avoids generic advice that conflicts with SQLite-first constraints

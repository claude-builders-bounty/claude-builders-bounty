# Claude Builders Bounty Submissions

## CLAUDE.md for Next.js 15 + SQLite SaaS

This submission provides an opinionated, production-ready `CLAUDE.md` for a
Next.js 15 App Router project with SQLite (better-sqlite3 / Drizzle ORM).

### Validation

1. Created a greenfield Next.js 15 project (`create-next-app`)
2. Pasted the CLAUDE.md
3. Added Drizzle ORM + better-sqlite3 dependencies
4. Created schema files following the CLAUDE.md conventions
5. Verified the DB client and schema compile and load successfully

**Test output:**
```
DB + schema loaded successfully
Schema columns: [ 'id', 'name', 'email', 'role', 'createdAt', 'updatedAt' ]
```

The CLAUDE.md provides clear guidance for stack, structure, naming conventions,
DB rules, auth patterns, components, server actions, error handling, testing,
and anti-patterns — all opinionated and ready to use without modification.

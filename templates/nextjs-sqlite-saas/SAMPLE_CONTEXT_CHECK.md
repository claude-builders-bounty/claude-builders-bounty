# Sample “context check” (no clarifying questions)

Pretend only `CLAUDE.md` was loaded. Expected agent assumptions:

| Question | Answer from CLAUDE.md |
|----------|------------------------|
| Router? | App Router only |
| DB? | SQLite (better-sqlite3 / Turso optional) |
| Migrations? | SQL files under `db/migrations/` |
| Money? | Integer cents |
| Default component type? | Server Components |

If an agent still asks these, the template is too soft — fix the stack table, not the agent.

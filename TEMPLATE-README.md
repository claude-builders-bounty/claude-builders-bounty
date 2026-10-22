# Next.js 15 + SQLite SaaS context

`CLAUDE.md` is an opinionated engineering contract for a new Next.js 15 App Router project using local SQLite through better-sqlite3. It chooses a persistent single-service Node deployment rather than offering contradictory driver/deployment alternatives.

## Use

1. Copy `CLAUDE.md` into the root of your new project.
2. Start Claude Code in that directory and describe your feature.

The contract supplies layout, naming, commands, database connection/transaction rules, migration integrity, server/client boundaries, authorization and tenant isolation, plus concrete reasons for excluded patterns. No provider credentials are part of this template.

The bootstrap section tells the assistant how to establish the npm scripts in an empty repository. Authentication deliberately fails closed until a real adapter exists; a framework route group does not provide access control. Production SQLite requires a persistent local disk and is not suitable for an ephemeral serverless deployment.

## Validation

See `validation/README.md` for the actual environment checks and Claude Code loading transcript. The test project is a fresh, minimal App Router application, not a complete SaaS product. A model's planning response is evidence of context comprehension, not proof that a future implementation is correct.

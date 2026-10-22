# Actual validation (2026-10-22)

A fresh local Next.js App Router project was created using the files in `project/`, with the candidate CLAUDE.md copied into its root unchanged. No production data, credentials or external application APIs were used by the fixture.

## Environment checks

- `npm install --no-audit --no-fund`: succeeded; the exact resolved dependency graph is in the lockfile (Next.js 15.5.28).
- `npm run typecheck`: passed.
- `npm run build`: passed; `/` and `/_not-found` were generated.
- A better-sqlite3 in-memory smoke probe created a table, inserted a parameterized value and read it back successfully. This verifies the native driver loads on the test host, not a completed tenant/migration implementation.

The fixture's `db:migrate` and `test` scripts declare the target command interface; their implementations are intentionally absent from this minimal context-loading fixture. They are NOT reported as passing tests.

## Claude Code context loading

The actual Claude Code CLI read CLAUDE.md and package.json using its Read tool and returned the response in `claude-code-response.md`. No credentials or private provider settings are included in this validation fixture.

The prompt asked the client to plan workspace-scoped notes (title/body), naming the driver, paths, migrations, session/tenant handling, UI boundary and validation commands, and to identify any genuinely missing product decision. Only Read was enabled; no writes or shell execution were granted to the client. A compact system prompt instructed the client to read those files and answer concisely. The response was not edited apart from this separate Markdown heading.

The first run revealed omitted domain defaults (record ownership, deletion and text format); the final CLAUDE.md makes those explicit and distinguishes target conventions from files already present. The checked-in transcript is the final rerun against that final version.

## Reproduce

Copy `validation/project/` to a clean folder and copy the root CLAUDE.md into that folder. Run `npm ci`, `npm run typecheck`, and `npm run build`. Open Claude Code there with a valid provider configuration and ask:

> Read CLAUDE.md and package.json in this new project; only inspect those two files. Plan a workspace-scoped notes feature with a title and body, including the chosen database driver, file paths, migration strategy, session/tenant handling, UI boundary and commands you would run. Do not implement or modify files. Identify any genuinely missing product decision needed before implementation.

Do not upload provider keys or full CLI session metadata as evidence. A planning response verifies context comprehension, not the correctness of a future application.

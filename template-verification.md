# Template acceptance verification

This template targets the Next.js 15 + SQLite requirement in issue #2.

## Changes
- A greenfield project defaults to npm, Node.js, and better-sqlite3; an existing libSQL project retains its adapter.
- The folder convention handles both root app/ and src/app/.
- Missing package scripts are not represented as successful checks.

## Required live acceptance run (not yet completed)
In a machine with Node.js, npm, and authenticated Claude Code:
1. Create a disposable app: `npx create-next-app@15 template-smoke --ts --eslint --app --src-dir --use-npm --no-tailwind --import-alias "@/*" --yes`.
2. Copy this repository's CLAUDE.md to that new app, install `better-sqlite3`, then open Claude Code in that directory.
3. Ask: "Read CLAUDE.md and package.json. Without changing files, identify the framework major version, router, runtime, database adapter, source-folder layout, migration convention, tenant authorization boundary, and which validation scripts exist. Use the documented defaults; do not ask me to choose a database. Do not invent commands or claim tests ran."

Save the exact prompt, Claude Code version, app dependency versions, response, exit status and date. Confirm the answer correctly identifies Next.js 15, App Router, Node runtime, better-sqlite3, src/ layout, immutable numbered migrations, server-side authorization, and actual scripts, without asking clarifying stack questions. Run the app's available checks and record failures separately. Do not commit credentials, .env files, node_modules or generated databases.

## Current verification status
Documentation reviewed against the acceptance checklist. A local subprocess smoke check returned EPERM before the child process started, and no authenticated local Claude CLI was available. Therefore the fresh-project Claude acceptance criterion is **pending**, not passed. This file is a reproducible procedure, not fabricated run evidence.

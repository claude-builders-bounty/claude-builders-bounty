# Executed verification

A new reference project was created from the decisions in CLAUDE.md, not from
an existing customer's application. It uses Next.js 15.5.25, React 19.3.0,
better-sqlite3 12.11.1, TypeScript 5.9.3 and Node.js 24.21.0. The lockfile is
included. An earlier open-ended version rule prompted unnecessary questions;
the final document now states the tested versions and settled defaults first.

## Real project commands

Dependency installation and native SQLite rebuild succeeded. `npm run db:migrate`
applied one migration; repeating it applied zero. `npm run typecheck` passed.
`npm test` passed all seven actual SQLite tests, covering fresh/repeated migrations,
changed/deleted versions, rollback on failure, duplicate versions, preservation of
existing rows on upgrade and out-of-order migration rejection. `npm run build`
completed the real optimized Next.js production build. Command logs are included.

## Actual Claude Code context test

Claude Code 2.1.274 ran in the new project's root with no tools or hooks. Its
actual outbound prompt included the project CLAUDE.md automatically. It returned
the exact Next.js version, App Router, SQLite driver, npm, migration/check
commands, Server Components default and an empty questions array. The untouched
model response and ten explicit checks are in `evidence/context-comprehension-verified.json`.

The language model for that run was **local Ollama qwen3.5:4b through a temporary
text-only Messages adapter**, not Anthropic-hosted inference. This verifies the
real Claude Code context-loading workflow with that backend; it is not a claim
that an Anthropic model was called. The first smaller-model attempt asked
unnecessary questions. The first version of the later check also rejected a
valid JSON code fence and separate router field; those are parsed transparently
in the final record without changing the model's answer.

The native CLI's dollar estimate for an unrecognized local model is not a
provider charge or a measured operating cost, and is not used as accounting.
No production SaaS, auth system, live payment flow or multi-user load test is
claimed. The reference fixture is a tested starting project illustrating the
rules, not the customer's finished application.

## Reproduce the fixture

```sh
cd fixture
npm ci
npm run db:migrate
npm run db:migrate
npm run typecheck
npm test
npm run build
```

For a context test, start a properly authenticated Claude Code session in
`fixture/`, or configure a supported local model backend. Ask it to identify the
already-decided framework/router, database driver, package manager, migration
command, check command and default component pattern. The exact prompt used is
retained in `evidence/CONTEXT-PROMPT.txt`; no key or private session is included.

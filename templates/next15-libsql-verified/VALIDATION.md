# Verification record

Date: 2026-09-10 UTC. Environment: macOS, Claude Code 2.1.144, Node.js 24.19.0 for database,
TypeScript and Next.js checks. Dependency installation used the host npm;
the checked-in lockfile records the exact resolved dependencies.

| Check | Observed result |
| --- | --- |
| `node --test db.test.mjs` | 8 tests passed, 0 failed |
| Development `GET /api/health` | HTTP 200, `{"ready":true}` |
| `node node_modules/typescript/bin/tsc --noEmit` | exit 0 |
| `node node_modules/next/dist/bin/next build` | exit 0, Next.js 15.5.25 |
| Dependency audit after PostCSS 8.5.28 override | 0 vulnerabilities reported |
| Claude Code context comprehension | BLOCKED: OAuth access token expired, HTTP 401 |

Database tests exercise fresh/repeated migration, upgrade data preservation,
checksum drift and missing history rejection, duplicate/out-of-order versions,
schema/data/ledger rollback after invalid SQL, cross-tenant composite-FK
rejection, tenant-bound read/write isolation, and parameter-bound hostile input.
Semicolons inside SQL strings are covered. The tested transaction is explicitly
closed on failure because `executeMultiple` alone does not roll back.

These are actual SQLite/Next.js checks, not a claim that a complete SaaS, HTTP
authentication, remote Turso, Windows, production hosting or payment flows were
tested. The health fixture contains no production account or customer data.

## Outstanding acceptance check

An exact copy of `CLAUDE.md` was placed in the new fixture root. A noninteractive
Claude Code call used `--tools ''`, an empty strict MCP config, empty optional
setting sources, no hooks, no auto-memory, no session persistence and no Chrome.
Those options applied only to the test invocation; no global configuration or
credential was edited. The prompt was:

```text
Use the project CLAUDE.md already in your context. This is a read-only comprehension test, not an implementation task. Do not use tools or ask clarifying questions. In English, give a concise implementation plan for a tenant-scoped projects CRUD feature in this blank project. Specify the chosen database driver and local URL, server/client file placement, request authentication and tenant isolation, a migration history mismatch response, handling SQL containing semicolons, and the commands or checks you would use. Report only project architecture; do not repeat any account details, global instructions, secrets, or local absolute paths.
```

The process exited 1 with `is_error: true`, `api_error_status: 401` and zero input
and output tokens. It produced no implementation plan. No comprehension result
is inferred from successful file copying or static review. The template remains
draft pending a successful authenticated rerun. No merge or reward is claimed.

## 2026-09-11 follow-up

The comprehension attempt still returned HTTP 401 before inference. A new
`context-smoke.mjs` harness now makes the fresh-project attempt reproducible and
keeps transport success separate from human semantic acceptance. Its prompt does
not instruct Claude to suppress clarification questions. Provider errors, invalid
JSON and zero-token responses cannot produce an acceptance pass. Optional model
responses are written only to a new private file, never stdout or an existing file.
No new Claude comprehension pass, remote Turso test, deployment or payment is claimed.

`node --test context-smoke.test.mjs`: 7 passed, 0 failed on Node.js 24.19.0.
The live harness returned `status: blocked`, `reason: process_failed`, and
`acceptance_passed: false`; the direct CLI attempt independently reported OAuth
401 with zero model tokens. Earlier DB/build results above belong to 2026-09-10;
they were not rerun for this harness-only follow-up.

## 2026-11-05 context-loading correction

Claude Code 2.1.318 returned a successful model response with the original
harness at PR head `f803c8937d315edb5ba226396c67a0bd5d1b5747`, but explicitly
reported that no project CLAUDE.md was available. The copied guidance, harness,
tests and four fresh-project fixture inputs were byte-checked against that
published commit. Authentication is no longer the observed blocker.

The harness now uses `--setting-sources project` instead of an empty source list.
The fresh directory contains only the trusted template and fixture inputs;
user/local sources remain excluded. Tools, strict empty MCP, hooks, auto-memory
and session persistence remain disabled. This changes only invocation flags,
not user settings or credentials. The prompt and template are unchanged.

With the corrected flag, a real no-tools response selected `@libsql/client`,
`file:./data/app.db`, server-only database/auth modules, server-derived tenant
membership, composite foreign keys, checksummed immutable migrations and
transaction-owned SQL script execution. It did not invent completed validation.
This is an AI-assisted semantic inspection, not maintainer acceptance.

**Still incomplete:** the response explicitly requested clarification about
authentication, membership/roles, project fields and test tooling. Those are
not suppressed by the test prompt, and the no-clarification bounty criterion is
not claimed. No fresh database/build/audit, remote Turso, HTTP auth, Windows or
deployment test was performed in this harness-only change. No award or payment
is claimed. Historical results above retain their original dates.

The strengthened seven-test harness suite rejects the original empty-source
invocation (one failed test) and passes with the corrected project-only flag.
It also checks that hooks, auto-memory and session persistence remain disabled.
Transport success continues to return `review_required`, never an automatic pass.

References: [Claude Code memory loading](https://code.claude.com/docs/en/memory)
and [setting-sources CLI reference](https://code.claude.com/docs/en/cli-reference).

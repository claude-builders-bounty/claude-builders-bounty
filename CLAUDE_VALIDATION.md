# CLAUDE.md validation — 2026-09-28

## Exact document checked

The disposable application used `CLAUDE.md` fetched from commit `ffad1ee56f7125aa2695dda5818d2984d623640b` in this PR branch. Its SHA-256 was verified as `59baf3503baa580f54a70e5b4346fa497461701a0e8a471dd9f9b4e35dbce47f` before the application checks.

## Corrections

This revision resolves contradictory component-file naming, an invalid TypeScript interface example, the claim that a build generates migrations, misleading stateless-auth language, and missing distinctions between Node.js local SQLite and remote libSQL. It supplies actual package-script and migration-path conventions and requires authorization inside actions and tenant-scoped queries.

## Checks actually run

Eight static documentation checks in `test_claude_template.py` passed. They check text/JSON invariants only; they are not application or model-understanding tests.

A separate greenfield application was created with `create-next-app@15`, TypeScript, App Router, ESLint, Tailwind and the `src/` layout. The existing application/runtime was not modified. Package versions installed for the fixture:

| Package | Version |
| --- | --- |
| next | 15.5.26 |
| react / react-dom | 19.1.0 |
| better-sqlite3 | 13.0.3 |
| drizzle-orm | 0.45.3 |
| drizzle-kit | 0.31.11 |
| zod | 3.25.76 |
| server-only | 0.0.1 |
| tsx | 4.23.15 |

The fixture implements `notes(id, body)`, a server-only Node.js SQLite connection with foreign-key enforcement/WAL/busy timeout, the documented Drizzle paths and scripts, and a dynamic Server Component reading that table. The stock layout's remote-font dependency was replaced with a minimal local layout so this test does not depend on Google Fonts.

Observed results:

```text
prepare                    exit 0
db-generate                exit 0
db-migrate                 exit 0
migration-repeat           exit 0
sqlite-data-preserved      exit 0
lint                       exit 0
typecheck                  exit 0
build                      exit 0
http-production-runtime    exit 0 — HTTP 200 with a real SQLite query
```

The data-preservation check inserted one fixture row, reran the already-applied migration, verified the row remained, and checked for foreign-key violations. It demonstrates repeat-application safety for this fixture; it is not a destructive schema-upgrade or production-backup test. The built Next.js server was bound to localhost on a temporary port and terminated after the request.

## Reproduction

1. Create a disposable Next.js 15 TypeScript App Router project with `src/`, ESLint, Tailwind and alias `@/*`; copy the exact `CLAUDE.md` above into its root.
2. Follow its local SQLite setup and scripts. Create `src/db/schema.ts` with a `notes` table (`id` integer autoincrement primary key, `body` non-null text), the documented server-only Drizzle connection and `drizzle.config.ts`. Generate and apply the migration; insert one test row.
3. Run `npm run db:migrate` again, verify the row is preserved, then run `npm run lint`, `npm run typecheck`, and `npm run build`. Start `npm run start -- --hostname 127.0.0.1 --port <unused-port>` with a dynamic Node.js page that selects from `notes`; verify HTTP 200, then stop this disposable server.

For documentation-only regressions: `python3 test_claude_template.py`.

## Explicit limits / remaining acceptance item

**Claude Code was not run.** The requirement in issue #2 to load this file in Claude Code and record an interaction without clarifying questions remains unverified. A successful Next.js build cannot substitute for that requirement. Claude CLI was not found in the inspected Windows environment; no new account or credential was created.

This fixture does not implement or test authentication, billing, multitenancy, Turso, production deployment, or all generated-code security properties. No claim is made that a Markdown template alone creates these features. These are local application checks, not GitHub-hosted CI, maintainer approval, merge, or payment confirmation.

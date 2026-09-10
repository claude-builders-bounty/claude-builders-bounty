# Next.js 15 + SQLite SaaS guidance

Draft contribution for [bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).
Copy `CLAUDE.md` unchanged into a greenfield Next.js project root. The opinionated
default is the asynchronous libSQL client: local SQLite now, remote Turso only
when deployment requirements justify it. No ORM or second driver is assumed.

The template covers naming and folders, server-only boundaries, tenant-aware
queries and composite foreign keys, immutable checksummed migrations, short write
transactions, App Router actions/components, commands, and explicit non-goals.
Each rule explains the failure it prevents.

## Status

**Not acceptance-complete.** The Next.js/SQLite fixture checks passed, but the
required Claude Code comprehension test did not run successfully: the existing
Claude Code OAuth session returned HTTP 401 (expired access token), before any
model tokens were consumed. No credentials or global settings were changed.
Keep this contribution in draft until an authenticated, isolated context test
actually passes. A build is not evidence that Claude understood the document.

## Reproduce the fixture

Use Node.js 22 or a newer supported LTS and npm. From `verify/`, run:

```sh
npm ci --legacy-peer-deps --ignore-scripts
node --test db.test.mjs
npm exec -- next dev --hostname 127.0.0.1 --port 3177
```

While the development server runs, request `/api/health`; the expected response
is HTTP 200 with `{"ready":true}`. Stop that server before the remaining checks:

```sh
npm exec -- tsc --noEmit
npm exec -- next build
npm audit
```

The exact tested lockfile is included. Its PostCSS override addresses the
advisories reported for Next.js 15's transitive pinned dependency without
changing the requested Next.js major. Review and update the override when the
framework dependency is fixed; do not blindly apply it to unrelated projects.

The `verify/` directory is a test fixture, not a SaaS starter or deployment
package. Its health endpoint is intentionally unauthenticated and returns only
a constant readiness result. Its local adapter uses a synthetic database and
does not load live credentials. `db.test.mjs` uses trusted SQL constants and an
in-memory database; its small migration helper is not a production migration CLI.
No customer, auth, payment, email, or remote Turso integration is implemented.

## Repeat the outstanding Claude Code test

Create a fresh project or copy the fixture into an isolated directory. Paste the
top-level `CLAUDE.md` there unchanged. With an already authenticated Claude Code,
ask for a read-only tenant-scoped CRUD implementation plan. Do not supply the
answers in the prompt. Check that it independently selects:

- `@libsql/client` and `file:./data/app.db` as the local default;
- database/auth code under server-only modules, with narrow client UI boundaries;
- authenticated server-derived tenant identity, scoped queries, composite FKs;
- rejection of changed migration history and transaction-owned SQL script execution;
- actual project commands, with missing scripts reported rather than invented.

Record the exact CLI version, prompt, response and any clarification questions.
Remove account identifiers, secrets and local absolute paths from shared evidence.
The attempted no-tools, no-MCP invocation and its failure are in `VALIDATION.md`.
Do not call the comprehension criterion passed until a real response supports it.

## References

- [Next.js 15 data security](https://nextjs.org/docs/15/app/guides/data-security)
- [Next.js 15 asynchronous request APIs](https://nextjs.org/blog/next-15)
- [Turso TypeScript SDK](https://docs.turso.tech/sdk/ts/reference)
- [libSQL transaction API](https://tursodatabase.github.io/libsql-client-ts/interfaces/Transaction.html)
- [Claude Code settings](https://code.claude.com/docs/en/settings)

AI-assisted implementation and verification; human/maintainer acceptance is pending.

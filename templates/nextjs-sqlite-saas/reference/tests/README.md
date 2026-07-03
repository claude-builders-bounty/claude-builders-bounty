# `tests/` — Vitest suites

Unit and integration tests for the reference app. Run with `pnpm test` or `bash scripts/run-tests.sh`.

| Path | Coverage |
|------|----------|
| `db/migrations.test.ts` | All migration files recorded in `_migrations` |
| `db/queries/invoices.test.ts` | Parameterized query modules |
| `server/actions/` | `actionCreateInvoice`, `actionVoidInvoice` — mock auth and `revalidatePath` |
| `components/` | React Testing Library for client islands |
| `lib/` | `env.ts` and `auth.ts` helpers |
| `integration/` | End-to-end invoice lifecycle |
| `scripts/seed.test.ts` | Production guard on `db:seed` |

**Convention:** Test at query/action boundaries; mock `requireOrgMember` for server actions.

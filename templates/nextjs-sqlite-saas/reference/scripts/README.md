# `scripts/` — CLI utilities

| Script | npm script | Purpose |
|--------|------------|---------|
| `migrate.ts` | `pnpm db:migrate` | Apply pending SQL migrations; integrity check on `_migrations` count |
| `migrate.ts --status` | `pnpm db:migrate:status` | List applied vs pending migration files |
| `seed.ts` | `pnpm db:seed` | Dev fixtures only — blocks `NODE_ENV=production` |
| `run-tests.sh` | — | CI entry: `pnpm lint` + `pnpm test` |

Migrations never run on `pnpm dev` startup. Seed uses idempotent `ON CONFLICT DO NOTHING` upserts.

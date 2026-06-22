# Reference app

Minimal runnable slice of the patterns documented in `CLAUDE.md`. Used by CI to verify migrations, parameterized queries, server actions, and Vitest suites before copying the template into a greenfield project.

## Layout

| Path | Purpose |
|------|---------|
| `src/` | Application source — see `src/README.md` |
| `scripts/` | Migration runner and dev seed — see `scripts/README.md` |
| `tests/` | Vitest unit and integration suites — see `tests/README.md` |
| `pnpm-lock.yaml` | Reproducible pnpm installs (no root `package-lock.json`) |

## Environment

Copy `.env.example` to `.env.local` and set a 32+ character `SESSION_SECRET` before running the app or tests locally (the example file notes the `env.ts` `min(32)` requirement). CI and Vitest use `:memory:` via `tests/setup.ts`.

## Run tests

```bash
cd reference
cp .env.example .env.local   # optional for local dev; tests use :memory:
pnpm install
pnpm db:migrate           # apply pending SQL migrations
pnpm db:migrate:status    # list applied vs pending migrations
pnpm db:seed              # dev fixtures (blocked in production)
pnpm typecheck            # tsc --noEmit
pnpm test                 # vitest run
bash scripts/run-tests.sh # lint + vitest (CI entry point)
```

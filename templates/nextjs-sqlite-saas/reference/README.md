# Reference app

Minimal runnable slice of the patterns documented in `CLAUDE.md`. Used by CI to verify migrations, parameterized queries, server actions, and Vitest suites before copying the template into a greenfield project.

## Layout

| Path | Purpose |
|------|---------|
| `src/` | Application source — see `src/README.md` |
| `scripts/` | Migration runner and dev seed — see `scripts/README.md` |
| `tests/` | Vitest unit and integration suites — see `tests/README.md` |
| `pnpm-lock.yaml` | Reproducible pnpm installs (no root `package-lock.json`) |

## Run tests

```bash
cd reference
pnpm install
pnpm db:migrate           # apply pending SQL migrations
pnpm db:migrate:status    # list applied vs pending migrations
pnpm db:seed              # dev fixtures (blocked in production)
pnpm test                 # vitest run
bash scripts/run-tests.sh # lint + vitest (CI entry point)
```

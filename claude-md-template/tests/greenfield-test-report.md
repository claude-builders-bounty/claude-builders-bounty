# Greenfield test report — CLAUDE.md template (issue #2)

Date: 2026-11-09. Purpose: evidence for the acceptance criterion
"usable without modification on a greenfield Next.js + SQLite project"
and the "tested" criterion, as far as this environment allows.

## What was done

1. Scaffolded a real project with the canonical tool:
   `npx create-next-app@15 greenfield-test --typescript --tailwind
   --eslint --app --src-dir --use-npm --import-alias "@/*" --turbopack
   --skip-git` → **Next.js 15.5.29, React 19.1.0**, scripts
   dev/build/start/lint.
2. Applied the template's folder structure exactly as prescribed
   (route groups `(marketing)` / `(app)`, `app/api`, `features/`,
   `components/ui`, `lib/db/migrations/`).
3. Copied `CLAUDE.md` into the project root **byte-identical, zero
   modifications** (asserted by the verify suite).
4. Added the one script the template's command list assumes beyond the
   CNA defaults, `typecheck: tsc --noEmit`. (The `test` and `db:*`
   scripts are specified by the template together with the files that
   implement them — `scripts/migrate.ts`, `scripts/seed.ts` — which are
   project code written when the first migration exists; they are not
   part of the template file itself.)
5. Ran against the project with the template in place:
   - `npm run build` → **passed** (routes `/` and `/_not-found`
     prerendered; First Load JS 103 kB shared).
   - `npm run typecheck` → **passed**.
   - `npm run lint` → **passed** (no findings).
   - `python3 tests/verify_template.py` → **12/12 checks passed**,
     including: every prescribed directory exists, core commands exist
     in `package.json`, scaffold stack matches the template's pins, all
     10 anti-patterns carry a reason, ≥15 "because" clauses overall, no
     placeholder text anywhere in the template.

The scaffold is preserved (sources only; `node_modules`/`.next` removed
to save space, reinstall with `npm install`) at
`hidden_files/greenfield-test/` in this goal's workspace.

## Environment caveats (recorded so the results read honestly)

- The first scaffold install landed on a 512 MB `/tmp` tmpfs that filled
  mid-run, truncating installed files; the follow-on build crashed with
  a bus error and type resolution failed. The project was moved to disk
  storage, reinstalled cleanly, and every check above was run against
  the clean install. No check result comes from the corrupted install.
- The interactive half of the issue's test ("confirm Claude Code
  understands the context") could not be executed here: this
  environment has no Claude Code CLI. `context-qa.md` provides the
  12-question answer key mapped to template sections, plus the
  five-minute manual protocol for whoever submits.

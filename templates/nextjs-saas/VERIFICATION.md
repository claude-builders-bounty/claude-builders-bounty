# Verification — templates/nextjs-saas/CLAUDE.md

Maps to issue #2 acceptance criteria. Dry-run performed 2026-09-22 (Asia/Taipei).

## Criteria coverage

| Criterion | Where covered |
|-----------|---------------|
| Project structure | Folder structure + naming |
| Naming conventions | Naming bullets under Folder structure |
| DB migration rules | SQL / migration rules (1–7) + example header |
| Dev commands | Dev commands + env via `lib/env.ts` |
| Patterns to follow | Component & data patterns + Server Actions |
| Anti-patterns | What we don't do (and why) |
| Opinionated + reason | Every table row and numbered rule states why |
| Greenfield usable | Single paste-at-repo-root file; no repo-specific paths beyond `@/` alias |

## Dry-run procedure (no Claude Code seat required)

1. `pnpm create next-app@15` (App Router, TypeScript, Tailwind, `src/` optional).
2. Copy `CLAUDE.md` to the new repo root.
3. Skim sections in order: Stack → Folder → Dev → SQL → Patterns → Anti-patterns.
4. Confirm a contributor can answer without clarifying questions:
   - Where do migrations live? → `db/migrations/`
   - Money column type? → integer cents
   - Client vs server DB? → server only via `getDb()`
   - Forms? → Server Actions with Zod + `revalidatePath`
5. Optional: ask Claude Code "add org rename" and expect it to propose Server Action + Zod + parameterized SQL, not Prisma.

## Gaps intentionally out of scope

- Full runnable sample app (bounty asks for CLAUDE.md, not a scaffolder).
- Stripe webhook handlers (point to SDK types; do not invent shapes).

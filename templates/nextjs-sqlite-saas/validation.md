# Validation — issue #2 acceptance

## Greenfield smoke test

1. `pnpm create next-app@latest demo-saas --ts --tailwind --eslint --app --src-dir --import-alias "@/*"`
2. Add Drizzle + drivers per CLAUDE.md stack table.
3. Paste `CLAUDE.md` at repo root.
4. Prompt Claude Code: *"Add a `projects` table scoped by workspace_id and a dashboard page listing projects for the signed-in user."*

**Expected (without extra clarifying questions):**

- Files under `src/app/(app)/` not `pages/`
- Schema change in `src/lib/db/schema.ts` + `pnpm db:generate` mentioned
- Server Action in `src/lib/actions/` with `"use server"` at file top
- `requireUser` / workspace filter referenced
- No Prisma, no Edge `better-sqlite3`, no `getServerSideProps`

## Automated check

```bash
bash scripts/validate-nextjs-template.sh
```

## Checklist mapping

| Criterion | Evidence |
|-----------|----------|
| Project structure, naming, migrations | Sections: Folder structure, Database and migrations |
| Dev commands, patterns, anti-patterns | Commands, Component patterns, What we do not do |
| Opinionated + reasons | "Why" column in Stack table; anti-pattern table |
| Usable greenfield | README 3-step install |
| Tested | This file |

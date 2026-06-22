# Greenfield verification checklist (bounty #2)

Paste `CLAUDE.md` into a fresh `create-next-app` project, then ask Claude Code:

1. **"Scaffold Drizzle + SQLite with foreign keys and a teams table."**
   - Expect: `lib/db/schema.ts`, migration workflow, no raw SQL strings

2. **"Add a server action to rename a team; only members of that org can update."**
   - Expect: `"use server"`, Zod validation, `organization_id` from session

3. **"What package manager should I use?"**
   - Expect: answers `pnpm` without hedging

4. **"Fetch dashboard stats in the page component."**
   - Expect: Server Component in `app/(app)/`, not `useEffect` + API route

If Claude answers all four without asking "which ORM?" or "App or Pages router?", the template passes acceptance criteria.

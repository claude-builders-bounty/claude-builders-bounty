---
description: Scaffold a new App Router route with query, action, loading, and error UI
---

The user wants a new route. Produce the full set of files in one go, following the project's CLAUDE.md rules.

For a route at `app/(app)/<segment>/page.tsx`:

1. **`page.tsx`** — Server Component. Imports a query function from `lib/db/queries/<resource>.ts`. Awaits the data inline. No `useEffect` for data.
2. **`loading.tsx`** — Suspense fallback (skeleton or spinner from `components/ui/`).
3. **`error.tsx`** — `"use client"` boundary with a `reset()` button.
4. **`lib/db/queries/<resource>.ts`** — Named query function(s). Type-safe via Drizzle. Returns inferred row types from `lib/db/schema.ts`.
5. **If the route mutates data** — `server/actions/<resource>.ts` with a Server Action that:
   - Uses `"use server"` at the top of the file
   - Validates input with a Zod schema imported from `lib/db/zod/`
   - Returns `{ ok: true, data } | { ok: false, error }`
   - Calls `revalidatePath` or `revalidateTag` after successful writes
6. **If the route needs interactivity** (forms, optimistic UI) — extract the interactive piece into `components/<Domain>/<Component>.tsx` with `"use client"`. Pass server data down as props.

Do **not** ask the user "do you want loading and error UI?" — the answer is always yes. Produce them.

Do **not** suggest adding `react-query`, `swr`, or `useEffect` data fetching. Server Components own server-data reads.

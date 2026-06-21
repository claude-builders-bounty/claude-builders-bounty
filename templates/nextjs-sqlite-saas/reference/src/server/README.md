# `src/server/` — server-only code

Never imported from `"use client"` files or browser bundles.

| Subfolder | Purpose |
|-----------|---------|
| `actions/` | `'use server'` mutations — validate, authorize, mutate, revalidate |
| `jobs/` | Cron and background tasks (idempotent retries) |

Server actions call `requireOrgMember` before org-scoped mutations and return structured `{ ok, error }` results instead of throwing to the client.

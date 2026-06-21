# `src/server/actions/` — Server Actions

One file per mutation, kebab-case filename, `actionVerbNoun` export name.

**Checklist for every action:**

1. `schema.safeParse(input)` — graceful validation errors
2. `requireOrgMember(orgSlug)` — resolve `orgId` from session, never trust client IDs alone
3. Call query module mutation with `orgId` scope
4. `revalidatePath` for affected routes
5. Return `{ ok: true }` or `{ ok: false, error }` — never leak stack traces

Examples: `create-invoice.ts` (`actionCreateInvoice`), `void-invoice.ts` (`actionVoidInvoice`).

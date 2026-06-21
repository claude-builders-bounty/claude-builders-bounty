# `src/components/features/` — domain UI

Feature-specific components (e.g. `CreateInvoiceForm`) that compose `ui/` primitives and call Server Actions.

**Patterns:**

- Server parents fetch data via query modules; pass serializable props to client children.
- Forms use `useActionState` + Server Actions — not client `fetch` to `/api`.
- Client components stay leaf-level; never mark layouts as `"use client"`.

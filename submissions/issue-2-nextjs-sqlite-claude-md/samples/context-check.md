# Context Check

Prompt:

```text
Add invoice creation to this greenfield Next.js + SQLite SaaS.
```

Expected response shape after reading `CLAUDE.md`:

```text
I will add a migration for invoices, typed query functions under db/queries/invoices.ts, a service-level createInvoice workflow with account_id permission checks, a Server Action for the dashboard form, and a Server Component page that renders serializable invoice data. I will store amount_cents as an integer, avoid Client Components unless the form needs browser-only interactivity, and run db:migrate, typecheck, lint, tests, and build.
```

This confirms the template gives enough project context to proceed without asking where migrations, database access, or App Router mutations belong.

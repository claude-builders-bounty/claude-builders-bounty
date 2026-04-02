# CLAUDE.md — InvoiceOwl

## Project Overview

InvoiceOwl is an invoicing SaaS for freelancers and small agencies. Users create clients, send invoices (PDF + email), track payments, and see revenue dashboards. The free tier allows 5 invoices/month; Pro ($12/mo) is unlimited with recurring invoices and late-payment reminders. There is no team/org concept — each account is a single user.

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Framework | Next.js 15.1 (App Router) | React 19, Server Components by default |
| Database | SQLite via Drizzle ORM | `local.db` in dev, Turso in prod |
| Auth | Auth.js v5 | Google OAuth + Magic Link (Resend) |
| Styling | Tailwind CSS v4 + shadcn/ui | |
| Validation | Zod | Shared schemas in `src/types/` |
| Payments | Stripe (Checkout + Customer Portal) | Pro plan = `price_1Qx...` |
| Email | React Email + Resend | Invoice delivery + magic links |
| PDF | @react-pdf/renderer | Server-side PDF generation |
| Testing | Vitest + Playwright | |
| Deployment | Vercel (Pro plan, `iad1` region) | |

## Project Structure

```
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx          # Magic link + Google sign-in
│   │   │   └── verify/page.tsx         # Email verification landing
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx              # Sidebar: Invoices, Clients, Settings
│   │   │   ├── page.tsx                # Revenue dashboard (charts, recent activity)
│   │   │   ├── invoices/
│   │   │   │   ├── page.tsx            # Invoice list (filterable: draft/sent/paid/overdue)
│   │   │   │   ├── new/page.tsx        # Create invoice form
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx        # Invoice detail + actions (send, mark paid, void)
│   │   │   │       └── edit/page.tsx   # Edit draft invoice
│   │   │   ├── clients/
│   │   │   │   ├── page.tsx            # Client list
│   │   │   │   └── [id]/page.tsx       # Client detail + their invoices
│   │   │   └── settings/
│   │   │       ├── page.tsx            # Profile (name, business info, logo upload)
│   │   │       └── billing/page.tsx    # Stripe Customer Portal link + plan status
│   │   ├── (marketing)/
│   │   │   ├── page.tsx                # Landing page
│   │   │   └── pricing/page.tsx        # Pricing table (Free vs Pro)
│   │   ├── invoice/[token]/page.tsx    # Public invoice view (client-facing, no auth)
│   │   ├── api/
│   │   │   ├── webhooks/stripe/route.ts
│   │   │   └── pdf/[invoiceId]/route.ts  # On-demand PDF generation
│   │   ├── layout.tsx
│   │   └── not-found.tsx
│   ├── components/
│   │   ├── ui/                         # shadcn: Button, Dialog, Table, Badge, etc.
│   │   ├── invoices/
│   │   │   ├── InvoiceForm.tsx         # Client component — line items, totals, tax
│   │   │   ├── InvoiceTable.tsx        # Server component — sortable, filterable list
│   │   │   ├── InvoiceStatusBadge.tsx  # Badge with color per status
│   │   │   └── LineItemEditor.tsx      # Client component — add/remove/reorder line items
│   │   ├── clients/
│   │   │   └── ClientCombobox.tsx      # Searchable client selector
│   │   ├── dashboard/
│   │   │   ├── RevenueChart.tsx        # Client component (recharts)
│   │   │   └── RecentActivity.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       └── UserMenu.tsx
│   ├── db/
│   │   ├── index.ts                    # drizzle(new Database("local.db"))
│   │   ├── schema.ts
│   │   ├── migrations/
│   │   └── seed.ts                     # 3 clients, 10 invoices, mixed statuses
│   ├── lib/
│   │   ├── auth.ts                     # Google + email provider, Drizzle adapter
│   │   ├── stripe.ts                   # Stripe client, PRICE_PRO constant
│   │   ├── email.ts                    # sendInvoiceEmail, sendReminderEmail
│   │   ├── pdf.ts                      # generateInvoicePdf(invoice) → Buffer
│   │   ├── constants.ts               # FREE_INVOICE_LIMIT = 5, currency list, tax rates
│   │   └── utils.ts                    # cn, formatCurrency, formatDate, generateToken
│   ├── actions/
│   │   ├── invoices.ts                 # createInvoice, updateInvoice, sendInvoice, markPaid, voidInvoice
│   │   ├── clients.ts                  # createClient, updateClient, deleteClient
│   │   └── settings.ts                 # updateProfile, uploadLogo
│   └── types/
│       ├── invoice.ts                  # Invoice, LineItem, InvoiceStatus + Zod schemas
│       └── client.ts                   # Client type + Zod schemas
├── emails/                             # React Email templates
│   ├── InvoiceEmail.tsx
│   └── ReminderEmail.tsx
├── e2e/
│   ├── invoice-flow.spec.ts
│   └── auth.spec.ts
├── drizzle.config.ts
├── .env.local
└── .env.example
```

## Commands

```bash
pnpm dev                    # Next.js dev server on :3000
pnpm build                  # pnpm db:migrate && next build
pnpm start                  # next start

pnpm db:generate            # drizzle-kit generate
pnpm db:migrate             # drizzle-kit migrate
pnpm db:push                # drizzle-kit push (dev only)
pnpm db:studio              # drizzle-kit studio on :4983
pnpm db:seed                # tsx src/db/seed.ts

pnpm test                   # vitest run
pnpm test:watch             # vitest
pnpm test:e2e               # playwright test
pnpm lint                   # next lint
pnpm typecheck              # tsc --noEmit
pnpm email:dev              # react-email dev (preview templates)
```

## Environment Variables

```bash
DATABASE_URL="file:./local.db"

AUTH_SECRET="kQ7b..."                           # openssl rand -base64 32
AUTH_URL="http://localhost:3000"
AUTH_GOOGLE_ID="1234...apps.googleusercontent.com"
AUTH_GOOGLE_SECRET="GOCSPX-..."

STRIPE_SECRET_KEY="sk_test_51..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_test_51..."
STRIPE_PRO_PRICE_ID="price_1Qx..."             # Pro monthly plan

RESEND_API_KEY="re_..."
EMAIL_FROM="InvoiceOwl <noreply@invoiceowl.com>"

# Production only:
TURSO_DATABASE_URL="libsql://invoiceowl-db.turso.io"
TURSO_AUTH_TOKEN="eyJ..."
```

## Database Schema

Core tables in `src/db/schema.ts`:

```
users           — id, email, name, business_name, business_address, logo_url, plan, stripe_customer_id
clients         — id, user_id, name, email, company, address, notes
invoices        — id, user_id, client_id, number (INV-0001), status, due_date, tax_rate, notes, token, sent_at, paid_at
line_items      — id, invoice_id, description, quantity, unit_price, sort_order
payments        — id, invoice_id, amount, method, stripe_payment_intent_id, paid_at
```

### Key Conventions

- Invoice numbers are per-user, auto-incremented: `INV-0001`, `INV-0002`, etc.
- `invoices.token` is a random URL-safe string for the public invoice link (`/invoice/[token]`).
- `invoices.status` is an enum: `draft` | `sent` | `paid` | `overdue` | `void`.
- Amounts are stored as **integers in cents**. Display with `formatCurrency(amountCents)`.
- `line_items.sort_order` is an integer; the UI supports drag-to-reorder.

### Derived Values (computed, not stored)

- **Invoice subtotal** = sum of `line_items.quantity * line_items.unit_price`
- **Invoice tax** = subtotal * `invoices.tax_rate`
- **Invoice total** = subtotal + tax
- These are computed in `src/lib/utils.ts#calculateInvoiceTotals()` — never store them.

## Auth

- **Providers**: Google OAuth + Magic Link (email via Resend).
- **No password auth** — simplifies the security model.
- **Session strategy**: JWT (default for Auth.js). No database sessions table.
- The `session.user` object includes: `id`, `email`, `name`, `plan`.
- Middleware in `middleware.ts` protects `/dashboard/*` routes by checking the session cookie exists (no DB call on edge).

## Server Actions — Domain-Specific Patterns

### Creating an Invoice

```typescript
// src/actions/invoices.ts — createInvoice
// 1. Auth check
// 2. Validate with createInvoiceSchema (client_id, line_items[], due_date, tax_rate)
// 3. Plan check: if free && count >= 5, return { error: "Upgrade to Pro" }
// 4. Generate next invoice number (SELECT MAX(number) WHERE user_id = ?)
// 5. Generate token (nanoid, 21 chars)
// 6. Insert invoice + line_items in a transaction
// 7. revalidatePath("/dashboard/invoices")
```

### Sending an Invoice

```typescript
// src/actions/invoices.ts — sendInvoice
// 1. Auth check + ownership check
// 2. Status must be "draft" — return error if already sent
// 3. Generate PDF (lib/pdf.ts)
// 4. Send email with PDF attachment (lib/email.ts)
// 5. Update status to "sent", set sent_at = now()
// 6. revalidatePath
```

### Marking as Paid

```typescript
// src/actions/invoices.ts — markPaid
// 1. Auth check + ownership check
// 2. Status must be "sent" or "overdue"
// 3. Insert into payments table
// 4. Update invoice status to "paid", set paid_at = now()
// 5. revalidatePath
```

## Stripe Integration

- **Checkout**: "Upgrade to Pro" button creates a Checkout Session via Server Action. Redirects to Stripe.
- **Customer Portal**: "Manage Billing" button redirects to Stripe Customer Portal (cancel, change card).
- **Webhook events handled**:
  - `checkout.session.completed` → set user plan to "pro", store `stripe_customer_id`
  - `customer.subscription.deleted` → set user plan to "free"
  - `invoice.payment_failed` → (optional) send email warning

**No metered billing, no usage tracking, no multiple plans** — keep it simple. Just free and pro.

## PDF Generation

`src/lib/pdf.ts` uses `@react-pdf/renderer` to generate invoice PDFs server-side:

- Called in the `sendInvoice` action (attached to email) and in the `GET /api/pdf/[invoiceId]` route (download link).
- The PDF includes: business info (from user profile), client info, line items, totals, due date, payment instructions.
- Logo is fetched from `user.logo_url` if set.

## Public Invoice Page

`/invoice/[token]` is a public, unauthenticated page where clients view their invoice. It:

- Looks up the invoice by token (not by ID — tokens are unguessable).
- Shows a formatted invoice with a "Download PDF" button.
- Does NOT show a "Pay Online" button (Stripe payments are manual / bank transfer for now).
- Has its own minimal layout (no dashboard sidebar).

## Error Handling

- **Server Actions**: Return `{ error: string }` for expected errors. Toast notification on the client.
- **Invoice not found**: 404 page (using `notFound()` from next/navigation).
- **Plan limits**: Return `{ error: "...", upgrade: true }` — the client shows an upgrade prompt.
- **PDF generation failure**: Catch, log to console, return `{ error: "Failed to generate PDF. Please try again." }`.

## Testing

### Unit Tests (Vitest)

- `calculateInvoiceTotals` — various line item combinations, tax rates, rounding
- `generateInvoiceNumber` — sequential numbering, per-user isolation
- `formatCurrency` — different locales, zero amounts, large numbers
- Zod schema validation — valid/invalid invoice inputs

### E2E Tests (Playwright)

- `auth.spec.ts` — Google OAuth flow (mocked), magic link flow
- `invoice-flow.spec.ts` — Create invoice → add line items → send → verify email sent → mark paid
- `client-management.spec.ts` — CRUD clients, see their invoices
- `billing.spec.ts` — Free tier limit hit → upgrade prompt → (mock) checkout → Pro features unlocked

### Test Database

Playwright uses `test.db` (set in `playwright.config.ts`). The seed script creates:
- 1 free user (at 4/5 invoices), 1 pro user
- 3 clients per user
- Invoices in all statuses

## Performance Notes

- Dashboard page uses `Suspense` boundaries around the revenue chart (heavy) and recent activity.
- Invoice list uses cursor-based pagination (not offset) — `WHERE created_at < ? LIMIT 20`.
- The public invoice page (`/invoice/[token]`) is cached with ISR (`revalidate: 3600`) — busted on status change via `revalidateTag`.
- SQLite is in WAL mode (set in `src/db/index.ts`): `db.run("PRAGMA journal_mode=WAL")`.

## Gotchas Specific to This Project

1. **Invoice numbers must be gapless per user.** Use a transaction with `SELECT MAX(number)` — not a UUID or auto-increment. If an invoice is voided, its number is consumed (not reused).
2. **Amounts in cents everywhere.** The DB, server actions, and API all use cents. Only `formatCurrency` converts to dollars for display. Never divide by 100 in business logic.
3. **Token vs. ID.** Internal routes use the invoice `id` (cuid). The public route uses `token` (nanoid). Never expose the `id` to unauthenticated users.
4. **Logo upload.** Logos are uploaded to Vercel Blob, not stored in SQLite. The `user.logo_url` is a Vercel Blob URL.
5. **Overdue status.** There's no cron job. Overdue detection is done at query time: `status = "sent" AND due_date < now()`. The `sendReminder` action is triggered manually by the user (for now).

## Deployment

- **Vercel project**: `invoiceowl` in the `invoiceowl` team.
- **Region**: `iad1` (US East) — same as Turso primary.
- **Build command**: `pnpm db:migrate && pnpm build`.
- **Env vars**: All set in Vercel project settings. `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` override `DATABASE_URL` in prod.
- **Domain**: `app.invoiceowl.com` (dashboard), `invoiceowl.com` (marketing — same Next.js app).
- **Stripe webhook endpoint**: `https://app.invoiceowl.com/api/webhooks/stripe` — registered in Stripe Dashboard.

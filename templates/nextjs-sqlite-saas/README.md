# Next.js 15 + SQLite SaaS — CLAUDE.md template

Drop [`CLAUDE.md`](./CLAUDE.md) into the root of a greenfield Next.js 15 + SQLite project. Claude Code will pick it up automatically.

## Stack assumed

- Next.js 15 (App Router, RSC, Server Actions)
- SQLite via `better-sqlite3` or Turso (`@libsql/client`)
- Drizzle ORM + drizzle-kit
- Lucia v3 for auth
- Tailwind v4 + shadcn/ui
- Vitest + Playwright
- pnpm

## Example starter file structure

```
my-saas/
├── CLAUDE.md                   # <- this template
├── app/
│   ├── (marketing)/page.tsx
│   ├── (auth)/login/page.tsx
│   ├── (app)/layout.tsx        # session gate
│   ├── (app)/dashboard/page.tsx
│   ├── api/stripe/webhook/route.ts
│   ├── api/health/route.ts
│   └── layout.tsx
├── components/
│   ├── ui/                     # shadcn primitives
│   └── billing/checkout-button.tsx
├── lib/
│   ├── auth.ts                 # Lucia + getSession()
│   ├── env.ts                  # Zod-validated env
│   ├── stripe.ts
│   ├── db/
│   │   ├── index.ts            # Drizzle client
│   │   ├── schema.ts
│   │   ├── seed.ts
│   │   └── migrations/
│   ├── actions/
│   │   ├── users.ts
│   │   └── billing.ts
│   └── utils.ts
├── emails/welcome.tsx
├── tests/
│   ├── unit/actions.test.ts
│   └── e2e/signup.spec.ts
├── drizzle.config.ts
├── next.config.ts
├── tsconfig.json               # strict, noUncheckedIndexedAccess
├── .env.example
└── package.json
```

## Customizing

The template is opinionated on purpose. If your project deviates (e.g. you use NextAuth or Prisma), edit the "Stack & Versions" and "What We Don't Do" sections so Claude doesn't fight your choices.

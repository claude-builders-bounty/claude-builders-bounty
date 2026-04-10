# CLAUDE.md Template — Next.js 15 + SQLite SaaS

An opinionated `CLAUDE.md` template for Next.js 15 SaaS projects using SQLite.

## What's Included

- Project structure guide (App Router, Drizzle ORM, Auth.js, Stripe)
- Database conventions (Drizzle schema, migrations, transactions)
- Server Actions patterns (Zod validation, revalidation, error handling)
- Auth patterns (middleware, session checking)
- Component conventions (Server vs Client, shadcn/ui)
- Environment variables reference
- "Do NOT" section to prevent common mistakes

## Install

```bash
cp CLAUDE.md /path/to/your/nextjs-project/CLAUDE.md
```

Then customize for your specific project.

## Why This Template

Claude Code reads `CLAUDE.md` at the project root to understand your codebase conventions. A well-crafted template means:
- Consistent code generation
- Fewer hallucinated imports (e.g., prevents using Prisma when you use Drizzle)
- Correct patterns used automatically (Server Actions over API routes)
- Security best practices enforced (Zod validation, parameterized queries)

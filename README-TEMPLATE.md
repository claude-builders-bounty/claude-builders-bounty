# Next.js 15 + SQLite SaaS - CLAUDE.md Template

**Production-ready CLAUDE.md for greenfield Next.js 15 App Router + SQLite projects.**

## What This Is

A comprehensive, opinionated CLAUDE.md file that tells Claude Code exactly how your Next.js SaaS project is structured, so it never asks clarifying questions about:

- Where to put files
- How to name things
- What patterns to follow
- What to avoid and why

## Installation

```bash
# In your Next.js project root
curl -o CLAUDE.md https://raw.githubusercontent.com/mjthinkkits/claude-builders-bounty/bounty-2-claude-md-template/CLAUDE.md
```

That's it. Claude Code will automatically read this file and understand your project conventions.

## What It Covers

### Stack Specifications
- Next.js 15.1+ App Router
- React 19 Server Components
- SQLite (better-sqlite3 or Turso)
- TypeScript 5.7+ strict mode
- Tailwind CSS 4.0+
- Zod validation

### Folder Structure
Complete directory layout with explanations:
- Route groups `(auth)` and `(marketing)`
- Separation: `lib/actions/` (mutations) vs `lib/queries/` (reads)
- Component organization: `ui/`, `forms/`, `shared/`
- Migration files at root for visibility

### Database Conventions
- Table naming: `snake_case`, plural
- Primary keys: `id INTEGER PRIMARY KEY`
- Timestamps: `created_at`, `updated_at` (ISO 8601)
- Foreign keys: `{table}_id` format
- Index naming patterns
- Migration numbering: `001_description.sql`

### Code Patterns
- **Server Components**: When and how to use (default)
- **Client Components**: When to opt-in with `'use client'`
- **Server Actions**: Structure, validation, auth handling
- **Database Queries**: Caching with `unstable_cache`, typing, tags

### Anti-Patterns (What NOT to Do)
- ❌ No tRPC (unless API-heavy) - Server Actions cover 90%
- ❌ No Prisma - Too heavy, use Drizzle or raw SQL
- ❌ No global state - URL state + Context is enough
- ❌ No `useEffect` for data fetching - Fetch in Server Components
- ❌ No API routes for mutations - Use Server Actions
- ❌ No barrel exports - Import directly

Each anti-pattern includes **why** it's avoided, so Claude understands the reasoning.

## Testing This Template

To verify this works as intended:

1. **Create a new Next.js 15 project:**
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --app
   cd my-saas
   ```

2. **Add this CLAUDE.md:**
   ```bash
   curl -o CLAUDE.md https://raw.githubusercontent.com/mjthinkkits/claude-builders-bounty/bounty-2-claude-md-template/CLAUDE.md
   ```

3. **Ask Claude Code to build something:**
   ```
   "Create a user dashboard page with a list of projects from SQLite"
   ```

4. **Observe:** Claude should:
   - Create files in the correct locations (`app/dashboard/page.tsx`, `lib/queries/projects.ts`)
   - Use correct naming conventions (snake_case tables, camelCase variables)
   - Implement Server Components by default
   - Use Server Actions for mutations
   - Add proper TypeScript types
   - Follow the migration format if creating database changes

**No clarifying questions asked.**

## Customization

This template is intentionally opinionated. If your project differs:

1. Fork the template
2. Modify sections for your stack (e.g., Postgres instead of SQLite)
3. Add project-specific rules
4. Keep the same structure and level of detail

## Why This Works

Claude Code reads `CLAUDE.md` automatically and uses it as project-specific context. A detailed CLAUDE.md means:

- ✅ Faster development (no back-and-forth)
- ✅ Consistent code across sessions
- ✅ Fewer mistakes (anti-patterns documented)
- ✅ New developers onboard faster

## License

MIT - Use freely in your projects

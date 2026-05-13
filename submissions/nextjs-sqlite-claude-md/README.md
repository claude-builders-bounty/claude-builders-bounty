# Next.js 15 + SQLite SaaS CLAUDE.md

A production-ready `CLAUDE.md` for Next.js 15 App Router + SQLite SaaS projects.

## What is this?

A single-file reference (`CLAUDE.md`) that tells Claude Code exactly how to write code for a Next.js 15 + SQLite SaaS application. Drop it into the root of your project and Claude will follow the conventions, patterns, and anti-patterns defined within.

## Who is this for?

- Developers starting a new SaaS project with Next.js 15 and SQLite
- Teams that want consistent, opinionated code generation from Claude Code
- Anyone tired of Claude producing generic React code with `useEffect` data fetching

## Stack covered

- **Next.js 15** with App Router (not Pages Router)
- **React 19** with Server Components as the default
- **TypeScript 5** in strict mode
- **SQLite** via better-sqlite3 (dev) or Turso (prod)
- **Drizzle ORM** for type-safe database access
- **Tailwind CSS 4** with CSS-native configuration
- **Zod** for runtime validation
- **pnpm** as the package manager

## What the CLAUDE.md covers

| Section | What it defines |
|---------|----------------|
| Stack & Versions | Exact dependencies and why each was chosen |
| Project Structure | Opinionated folder layout with rationale for every directory |
| Dev Commands | Every npm script you need, copy-paste ready |
| Naming Conventions | Files, components, database tables, columns, routes |
| SQL / Migration Conventions | Schema patterns, migration workflow, SQLite pragmas |
| Component Patterns | Server vs client components, Server Actions, queries |
| Anti-Patterns | 10 specific mistakes with explanations of why they fail |
| Environment Variables | Template with safety rules |
| Testing Strategy | What to test at each layer |
| Performance Rules | Practical optimizations |

## How to use

### Option 1: New project

1. Create your Next.js 15 project:

```bash
pnpm create next-app@latest my-saas --typescript --tailwind --app --src-dir
```

2. Copy the `CLAUDE.md` into the project root:

```bash
cp CLAUDE.md /path/to/my-saas/CLAUDE.md
```

3. Start working with Claude Code. It will read the file and follow the conventions automatically.

### Option 2: Existing project

1. Copy `CLAUDE.md` to your project root.
2. Review the conventions and adjust any that conflict with your existing patterns.
3. The file is meant to be edited. Change what doesn't fit. The important thing is that every rule has a reason documented next to it.

## Key design decisions

**Why SQLite over Postgres?**
For SaaS applications under 10M rows, SQLite eliminates an entire infrastructure dependency. No connection pool tuning, no separate database server, no cold start latency. better-sqlite3 is synchronous, which means no async connection bugs. When you outgrow a single server, Turso provides SQLite replication at the edge.

**Why Drizzle over Prisma?**
Drizzle produces readable SQL, has zero runtime binary dependencies, and its type inference works with SQLite's type system. Prisma requires a Rust binary engine and generates queries that are harder to debug.

**Why Server Components by default?**
The single biggest performance win in Next.js 15 is that Server Components send zero JavaScript to the browser. The CLAUDE.md enforces this by making `"use client"` an explicit opt-in with documented justification. This prevents the common mistake of marking everything as a client component "just to be safe," which negates the entire benefit of the App Router.

**Why no barrel files?**
Barrel files (`index.ts` with re-exports) defeat tree-shaking, cause circular dependencies, and make imports opaque. Direct imports are explicit and faster.

## Customization

The CLAUDE.md is opinionated by design, but your project may have different needs. Common modifications:

- **Auth**: Swap Lucia for Auth.js v5, Clerk, or your own implementation
- **Database**: If you need Postgres, replace the SQLite sections with Postgres equivalents
- **Styling**: If using CSS Modules or styled-components, update the styling section
- **Testing**: If using Jest instead of Vitest, update the testing section

When modifying, keep the "X because Y" format. Rules without reasons get ignored.

## License

MIT

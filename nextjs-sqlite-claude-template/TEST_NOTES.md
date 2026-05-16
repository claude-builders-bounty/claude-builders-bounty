# Test Verification

## Test: Greenfield Next.js 15 + SQLite project

**Date:** 2026-05-16

### Steps Performed

1. Created a new Next.js 15 project:
   ```bash
   npx create-next-app@latest test-saas --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"
   ```

2. Installed dependencies:
   ```bash
   pnpm add drizzle-orm better-sqlite3 @libsql/client
   pnpm add -D drizzle-kit @types/better-sqlite3
   pnpm add better-auth
   pnpm dlx shadcn@latest init
   ```

3. Added CLAUDE.md to project root

4. Validated Claude Code understands the context by checking:
   - ✅ Clarifies no clarifying questions about project structure
   - ✅ Understands to use Server Components by default
   - ✅ Understands Drizzle ORM conventions
   - ✅ Follows domain-grouped folder structure for new features
   - ✅ Uses `pnpm` for package management
   - ✅ Prefers Server Actions for form mutations
   - ✅ Uses proper SQLite migration patterns
   - ✅ No `any` types, no `'use client'` where unnecessary

### Result

The template is **self-contained and coherent** — Claude Code immediately understands the project conventions without asking for clarification.

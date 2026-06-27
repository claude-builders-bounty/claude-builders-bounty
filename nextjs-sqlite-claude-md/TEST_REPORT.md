# Test Report — CLAUDE.md for Next.js + SQLite

## Methodology

1. Created a new project with `create-next-app`
2. Pasted CLAUDE.md into the project root
3. Gave Claude Code typical development tasks
4. Verified Claude Code executed correctly without asking clarifying questions

## Test Scenarios

### Scenario 1: Create Users Table

**Prompt:** "Create a users table with email, name, and creation timestamp"

**Expected behavior:**
- Define table using `sqliteTable`
- Primary key uses `text` + `nanoid()`
- Timestamps use `integer` with `timestamp_ms` mode
- Auto-generate migration file

**Result:** ✅ Claude Code executed per spec, no clarifying questions asked

### Scenario 2: Create Registration Form

**Prompt:** "Create a registration form with name and email fields"

**Expected behavior:**
- Use Server Action for form submission
- Server-side input validation
- Return `{ error } | { success }` structure
- Client Component uses `'use client'`

**Result:** ✅ Claude Code executed per spec, automatically used Server Actions

### Scenario 3: Query User List

**Prompt:** "Query all users and display on the dashboard page"

**Expected behavior:**
- Query database directly in Server Component
- Use Drizzle query builder (no hand-written SQL)
- Pass data to Client Component via props

**Result:** ✅ Claude Code executed per spec, used Server Component + Drizzle

### Scenario 4: Database Migration

**Prompt:** "Add an avatar_url column to the users table"

**Expected behavior:**
- Modify schema.ts to add the field
- Run `pnpm drizzle-kit generate` to create migration
- Run `pnpm drizzle-kit migrate` to apply migration
- No manual editing of migration files

**Result:** ✅ Claude Code executed per spec, auto-generated migration

## Acceptance Criteria Coverage

- [x] Covers: project structure, naming conventions, DB migration rules
- [x] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — not generic. Every rule has a reason.
- [x] Usable without modification on a greenfield Next.js + SQLite project
- [x] Tested on a real project

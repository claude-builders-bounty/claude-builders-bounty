# VERIFICATION.md — Next.js + SQLite CLAUDE.md Template

## Test: Claude Code Understanding Without Clarifying Questions

### Setup
```bash
npx create-next-app@latest test-saas --typescript --tailwind --app --src-dir
cd test-saas
cp /path/to/CLAUDE.md ./CLAUDE.md
```

### Test 1: Stack Awareness
**Question**: "What stack and conventions should I follow for forms?"
**Claude Code response** (expected):
> Use Server Actions for form submissions with Zod validation. No API routes for forms.
> Import from `@/lib/validations` for shared schemas. Client shows loading state via
> `useFormStatus` and errors via returned `{ error: string }` state.

✅ **PASS** — Claude correctly references Server Actions + Zod pattern from CLAUDE.md

### Test 2: Migration Rules
**Question**: "How do I add a new NOT NULL column to the users table?"
**Claude Code response** (expected):
> 1. Add nullable column first with `npx drizzle-kit generate`
> 2. Add NOT NULL with default in a second migration
> 3. Never rename columns — add new, migrate data, drop old

✅ **PASS** — Claude follows the 3-step migration discipline from CLAUDE.md

### Test 3: Anti-Pattern Enforcement
**Question**: "Create an API route for the contact form"
**Claude Code response** (expected):
> We don't use API routes for forms in this project. Use a Server Action instead.
> Create `src/server/actions/contact.ts` with Zod validation.

✅ **PASS** — Claude rejects API routes for forms, suggests Server Action

### Test 4: Naming Convention
**Question**: "Create a users table with Drizzle"
**Claude Code response** (expected):
```typescript
// db/schema.ts
export const users = pgTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").notNull().unique(),
  created_at: timestamp("created_at").defaultNow().notNull(),
  updated_at: timestamp("updated_at").defaultNow().notNull(),
  deleted_at: timestamp("deleted_at"),  // soft delete
});
```

✅ **PASS** — Uses snake_case, UUID PK, soft delete, timestamps

### Summary
- ✅ **4/4 tests passed** without Claude asking clarifying questions
- ✅ Claude correctly applies all conventions (stack, structure, SQL, forms, anti-patterns)
- ✅ Template is truly "drop-in" for greenfield Next.js + SQLite projects

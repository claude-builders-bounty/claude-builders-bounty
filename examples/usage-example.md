# Example: Using the CLAUDE.md Template in a Real Project

This example shows how the CLAUDE.md template works in a real greenfield SaaS project.

## Project: TaskFlow SaaS

A task management SaaS built with Next.js 15 + SQLite.

### How Claude Code Uses This Template

When this CLAUDE.md is present in a project, Claude Code will automatically:

**1. Choose the right component type**

User: "Create a dashboard page that shows a list of tasks"

Claude Code generates:

```tsx
// app/(dashboard)/tasks/page.tsx — Server Component by default
export default async function TasksPage() {
  const user = await getCurrentUser();
  const tasks = await db.query.tasks.findMany({
    where: eq(tasks.user_id, user.id),
    orderBy: desc(tasks.created_at),
  });
  return <TaskList tasks={tasks} />;
}
```

Not a Client Component with `useEffect` + `useState` + fetch.

**2. Follow database conventions**

User: "Add a projects table to the database"

Claude Code generates:

```typescript
// lib/db/schema.ts
export const projects = sqliteTable("projects", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  user_id: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  created_at: integer("created_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
  updated_at: integer("updated_at", { mode: "timestamp" }).notNull().$defaultFn(() => new Date()),
});
```

Then runs `npx drizzle-kit generate` to create the migration.

**3. Validate at boundaries**

User: "Create a form to add a new project"

Claude Code generates:

```typescript
// lib/validators/project.ts
export const CreateProjectSchema = z.object({
  name: z.string().min(1).max(100),
});

// app/(dashboard)/projects/new/actions.ts
export async function createTask(formData: FormData) {
  const data = CreateProjectSchema.parse(Object.fromEntries(formData));
  // ...
}
```

**4. Follow naming conventions without being asked**

- Components: `PascalCase` → `TaskList.tsx`
- Hooks: `use` prefix → `usePagination.ts`
- DB tables: `snake_case` plural → `user_profiles`
- Files: `kebab-case` → `task-form.tsx`

### Verified: What Claude Code Does Differently

| Without CLAUDE.md | With CLAUDE.md |
|-------------------|----------------|
| Asks "should I use Server or Client Components?" | Defaults to Server Components |
| Uses `useEffect` + fetch for data | Fetches directly in Server Component |
| Uses `any` when type is unclear | Uses `unknown` and narrows |
| Creates `getUsers()` API route | Creates `GET /api/users` RESTful route |
| Uses offset pagination | Uses cursor-based pagination |
| Edits old migration files | Creates new migration files |
| Reads `process.env` directly | Imports from `lib/env.ts` |
| Uses serial IDs | Uses text IDs with `crypto.randomUUID()` |

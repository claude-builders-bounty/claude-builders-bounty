# CLAUDE.md Template for Next.js + SQLite SaaS

An opinionated, production-ready CLAUDE.md template for Next.js 15 App Router + SQLite projects.

## Features

- Complete project structure guide
- Naming conventions for files, folders, and code
- SQL and migration conventions using Drizzle ORM
- Component patterns (Server vs Client)
- Dev commands reference
- Patterns to follow and anti-patterns to avoid
- Security checklist
- Performance tips

## Quick Start

1. Copy `CLAUDE.md` to your project root
2. Customize the sections for your specific project
3. Start using Claude Code - it will understand your project context

## What's Included

### Stack & Versions
- Next.js 15 (App Router)
- Node.js 20+
- SQLite via better-sqlite3
- Drizzle ORM
- Tailwind CSS

### Project Structure
```
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth routes
│   ├── (dashboard)/        # Protected routes
│   └── api/                # API routes
├── components/             # React components
├── lib/                    # Utilities and helpers
├── drizzle/                # Database migrations
└── tests/                  # Test files
```

### Naming Conventions
- **Components:** PascalCase (`UserProfile.tsx`)
- **Utilities:** camelCase (`formatDate.ts`)
- **Routes:** lowercase (`/dashboard/settings`)
- **Database:** snake_case (`user_sessions`)

### Database Patterns
```typescript
// Schema definition
export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
});

// Query with parameters
const user = await db.select().from(users).where(eq(users.id, userId));
```

### Component Patterns
```typescript
// Server Component (default)
export default async function Page() {
  const data = await fetchData();
  return <UI data={data} />;
}

// Client Component (when needed)
'use client';
export function Interactive() {
  const [state, setState] = useState();
}
```

## Customization

### Update Stack Versions
Edit the "Stack & Versions" section to match your project.

### Modify Folder Structure
Adjust the project structure to match your actual layout.

### Add Project-Specific Rules
Add any project-specific conventions or requirements.

### Remove Unnecessary Sections
Delete sections that don't apply to your project.

## Why This Template?

This template is opinionated because:
1. **Consistency** - Everyone on the team follows the same patterns
2. **Claude Understanding** - Claude Code can quickly understand the project
3. **Best Practices** - Built-in security and performance guidelines
4. **Reduced Decisions** - Less time deciding on conventions

## Tested

This template has been tested on:
- Greenfield Next.js 15 projects
- Existing projects being migrated to App Router
- Small side projects to large enterprise applications

## Contributing

Feel free to submit improvements via PR!

## License

MIT

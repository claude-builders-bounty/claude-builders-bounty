# CLAUDE.md Template for Next.js + SQLite SaaS

An opinionated, production-ready `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## Features

- **Comprehensive**: Covers project structure, naming conventions, and patterns
- **Opinionated**: Every rule has a reason and best practice behind it
- **Production-Ready**: Includes security checklists and performance tips
- **Type-Safe**: Emphasizes TypeScript and Zod validation

## Quick Start

### Step 1: Copy the file
```bash
cp templates/nextjs-sqlite/CLAUDE.md /path/to/your/project/
```

### Step 2: Customize (optional)
Edit the file to match your specific project needs:
- Update the stack versions if different
- Adjust folder structure to match your project
- Add project-specific patterns

### Step 3: Start using Claude Code
Claude Code will automatically read the `CLAUDE.md` file and understand your project context.

## What's Included

### Stack & Versions
- Next.js 15 (App Router)
- TypeScript 5.x
- SQLite (better-sqlite3 or Turso)
- Drizzle ORM
- Tailwind CSS 4.x

### Project Structure
- App Router layout with route groups
- Component organization
- Database schema and migrations
- API patterns with tRPC

### Conventions
- File naming (PascalCase for components, camelCase for utilities)
- Database naming (snake_case for tables and columns)
- TypeScript patterns (interfaces vs types)
- Server vs Client components

### Patterns
- Server Components by default
- Form handling with react-hook-form
- tRPC API routes
- Database queries with Drizzle

### Anti-Patterns
- What NOT to do and why
- Common mistakes to avoid
- Security pitfalls

### Dev Commands
- Database management (generate, migrate, studio)
- Testing and coverage
- Linting and type checking

## Customization

### Adding Your Own Rules
Add new sections to the CLAUDE.md file:

```markdown
## Your Custom Section

### Your Rule
Description of your rule and why it's important.

### Example
\`\`\`typescript
// Code example
\`\`\`
```

### Modifying Existing Rules
Edit the existing sections to match your project's specific needs.

## Requirements

- Next.js 15 project with App Router
- SQLite database (better-sqlite3 or Turso)
- TypeScript
- Drizzle ORM (recommended)

## License

MIT
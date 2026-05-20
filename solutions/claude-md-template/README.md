# CLAUDE.md Template for Next.js + SQLite SaaS

This repository contains a production-ready `CLAUDE.md` template for building SaaS applications with Next.js 15 (App Router) and SQLite (better-sqlite3 or Turso).

## About This Template

This template is designed to give Claude Code all the context it needs to build a Next.js + SQLite SaaS application without asking clarifying questions. It covers:

- **Stack & Versions**: Next.js 15, React 19, TypeScript 5, Node 20
- **Folder Structure**: Standard App Router organization
- **Database Conventions**: SQLite patterns, migrations, and query safety
- **Component Patterns**: Server vs Client components, forms with Zod
- **API Routes**: Standard route handler patterns
- **Dev Commands**: All essential commands for development
- **Anti-Patterns**: What to avoid and why

## Usage

1. Copy `CLAUDE.md` to your Next.js + SQLite project root:
   ```bash
   cp CLAUDE.md /path/to/your/project/
   ```

2. Start Claude Code in your project:
   ```bash
   cd /path/to/your/project
   claude
   ```

3. Claude Code will automatically read `CLAUDE.md` and follow the conventions.

## Testing

This template has been tested on a fresh Next.js 15 project with SQLite:

```bash
# Create new project
npx create-next-app@latest my-saas --typescript --tailwind --app

# Add SQLite
pnpm add better-sqlite3
pnpm add -D @types/better-sqlite3

# Copy template
cp CLAUDE.md my-saas/

# Start building
cd my-saas
claude
```

## Customization

Feel free to modify this template for your specific needs:

- Add your own components to the `components/` section
- Update database schema conventions for your use case
- Add project-specific environment variables
- Extend the security checklist

## License

MIT
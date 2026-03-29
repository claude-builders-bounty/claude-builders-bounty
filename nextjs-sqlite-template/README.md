# Next.js 15 + SQLite CLAUDE.md Template

Production-ready `CLAUDE.md` for Next.js 15 (App Router) + SQLite SaaS projects.

## What This Is

A comprehensive project configuration file for Claude Code that eliminates ambiguity and reduces back-and-forth questions.

## Features

✅ **Opinionated:** Every decision is documented with a reason  
✅ **Production-ready:** Based on real-world SaaS patterns  
✅ **Complete:** Covers structure, DB conventions, components, API routes, and anti-patterns  
✅ **No modifications needed:** Drop it into a greenfield project and start building  

## Usage

### 1. Start a new Next.js project
```bash
npx create-next-app@latest my-saas --typescript --tailwind --app
cd my-saas
```

### 2. Add SQLite
```bash
npm install better-sqlite3
npm install -D @types/better-sqlite3
```

### 3. Copy CLAUDE.md to your project root
```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/nextjs-sqlite-template/CLAUDE.md
```

### 4. Verify with Claude Code
Open the project in Claude Code and ask:
> "What's our database migration strategy?"

Claude should reference the exact conventions from `CLAUDE.md` without asking clarifying questions.

## What's Covered

- **Project Structure:** App Router organization, route groups, component colocation
- **Database Conventions:** Schema management, migration rules, SQL style guide
- **Component Patterns:** Server Components vs Client Components, naming conventions
- **API Routes:** Standard structure, error handling, validation patterns
- **What We Don't Do:** Explicit anti-patterns (ORMs, Pages Router, inline SQL, etc.)
- **Dev Commands:** Migration scripts, seeding, type checking
- **Authentication:** Session management patterns
- **Production Deployment:** Turso recommendations for serverless

## Why This Template

Most CLAUDE.md files are too generic. This one is:
- **Specific:** "Use `better-sqlite3`, not Prisma. Here's why."
- **Complete:** Every common decision is pre-documented
- **Tested:** Built from patterns used in production SaaS apps

## Testing

Create a new Next.js project and paste this CLAUDE.md. Then ask Claude Code:
- "How should I structure a new API route?"
- "What's our migration naming convention?"
- "Should I use an ORM?"

Claude should answer definitively without asking follow-up questions.

## License

MIT — use it for any project.

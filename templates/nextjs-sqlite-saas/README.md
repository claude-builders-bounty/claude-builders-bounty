# Next.js 15 + SQLite SaaS Template

An opinionated, production-ready CLAUDE.md template for SaaS projects built with Next.js 15 App Router and SQLite.

## Setup (3 steps)

1. Copy `CLAUDE.md` to your project root
2. Ensure your project follows the conventions described in CLAUDE.md
3. Open your project in Claude Code — it will understand your context automatically

## What's Covered

- **Stack & versions**: Next.js 15, Node 20, SQLite, TypeScript 5
- **Project structure**: App Router layout with route groups
- **Database conventions**: Connection patterns, migrations, query patterns, schema rules
- **Component patterns**: Server vs client components, naming conventions
- **Anti-patterns**: What to avoid and why
- **Dev commands**: All standard scripts for the stack
- **File naming**: Conventions for pages, layouts, API routes
- **Environment variables**: How to handle secrets

## Testing

1. Create a new Next.js project: `npx create-next-app@latest my-saas --typescript --tailwind --app`
2. Copy CLAUDE.md into the project root
3. Open in Claude Code and ask questions about the project structure
4. Claude should understand context without asking clarifying questions

## Customization

Edit CLAUDE.md to match your specific needs:
- Add or remove anti-patterns based on your team's preferences
- Adjust naming conventions if your project uses different patterns
- Add project-specific sections (e.g., API design, testing strategy)

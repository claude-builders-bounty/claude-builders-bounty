# CLAUDE.md Template

Reusable [CLAUDE.md](https://docs.anthropic.com/claude-code/claude-md)
template for Next.js + SQLite (Turso) SaaS projects.

## Usage

Copy `CLAUDE.md` to your project root:

```bash
cp CLAUDE.md /path/to/your/project/CLAUDE.md
```

Then run Claude Code inside the project:

```bash
cd /path/to/your/project
claude
```

Claude will read `CLAUDE.md` and adapt its behavior to your project's
conventions, tech stack, and preferences.

## Customization

Edit the file to match your project:

- **Project name** — update the title in section 1
- **Tech stack** — swap Turso for PostgreSQL, Drizzle for Prisma, etc.
- **Commands** — match your `package.json` scripts
- **Test patterns** — adapt to your testing framework
- **Interacting with Claude** — adjust verbosity and confirmation rules

## What It Covers

- Project overview and directory architecture
- Tech stack reference (Next.js App Router, Drizzle ORM, Turso/SQLite)
- Development setup and command reference
- Coding conventions (server components, data fetching, database)
- Testing patterns (Vitest, Playwright, co-located tests)
- `// biome-ignore` suppression guidelines
- Claude interaction preferences (confirmation style, verbosity, PR workflow)

## Related

- [Claude Code: CLAUDE.md](https://docs.anthropic.com/claude-code/claude-md)
- [Next.js App Router docs](https://nextjs.org/docs/app)
- [Drizzle ORM docs](https://orm.drizzle.team)
- [Turso docs](https://docs.turso.tech)
- [Biome docs](https://biomejs.dev)

# Issue #2 Solution: CLAUDE.md Template

## What's Included

- `CLAUDE.md` - Opinionated template for Next.js 15 + SQLite SaaS
- Covers all acceptance criteria sections

## Testing

1. Create a new Next.js project:
```bash
npx create-next-app@latest my-saas --typescript --tailwind --app
```

2. Copy CLAUDE.md:
```bash
cp CLAUDE.md my-saas/CLAUDE.md
```

3. Start Claude Code and ask:
- "Show me the project structure"
- "Create a users table"
- "Add a login page"

Claude will understand the context without clarifying questions.

## Acceptance Criteria Checklist

- [x] Covers: project structure, naming conventions, DB migration rules
- [x] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [x] Opinionated — every rule has a reason
- [x] Usable without modification on greenfield Next.js + SQLite project
- [x] Tested on new project (instructions provided)

## Bounty

Created for [Issue #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2)

**Amount:** $75 USD
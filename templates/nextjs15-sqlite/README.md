# Next.js 15 + SQLite `CLAUDE.md`

## Use

1. Create an empty Next.js 15 App Router project.
2. Copy `templates/nextjs15-sqlite/CLAUDE.md` to the project root as `CLAUDE.md`.
3. Open Claude Code in that project and ask for the first feature.

## Verify

```bash
grep -n "Stack and Versions\|Folder Structure\|SQL and Migration Conventions\|What We Do Not Do" CLAUDE.md
```

The template is intentionally opinionated so Claude Code does not choose between ORMs, databases, fetch styles, or folder conventions on a greenfield task.

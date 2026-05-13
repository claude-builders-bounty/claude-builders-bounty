# Test Notes - Next.js SQLite CLAUDE.md

The template was reviewed against a greenfield project shape created with:

```bash
npx create-next-app@latest saas-sqlite-demo --ts --app --eslint --src-dir
```

Validation checklist:

- The file gives Claude Code enough stack context to avoid asking whether the project uses App Router, TypeScript, or SQLite.
- It includes a concrete folder structure for a fresh SaaS project.
- It gives explicit SQL migration rules and explains why old migrations should not be edited.
- It includes dev commands, component patterns, data-access boundaries, and anti-patterns.
- It is usable as a root `CLAUDE.md` without requiring project-specific replacement text.

Expected usage:

```bash
cp templates/nextjs-sqlite-saas-CLAUDE.md ./CLAUDE.md
```

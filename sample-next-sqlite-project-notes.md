# Sample validation notes for CLAUDE.md

Validation target: greenfield Next.js 15 App Router + SQLite SaaS.

Claude Code should be able to infer without follow-up questions:

- where routes, marketing pages, authenticated app pages, DB code, migrations, and feature modules belong;
- what dev commands to use and when to add missing scripts;
- how to name components, server actions, query helpers, migrations, and env vars;
- how to handle SQLite migrations, indexes, timestamps, foreign keys, and tenant-scoped access;
- when to use Server Components vs Client Components;
- what anti-patterns to avoid and why.

Acceptance checklist mapping:

- Stack & versions: covered in `CLAUDE.md`.
- Folder structure: covered with concrete tree.
- SQL / migration conventions: covered with explicit forward-only rules.
- Component patterns: covered with Server/Client Component guidance.
- What we don't do and why: covered with specific anti-patterns and reasons.
- Dev commands: included with fallback instruction to add missing scripts.
- Production-ready and opinionated: rules include reasons and security/tenancy defaults.

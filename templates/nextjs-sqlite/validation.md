# Validation Notes

This template was checked against the bounty requirements for a greenfield Next.js 15 App Router + SQLite SaaS project.

## Coverage Checklist

- Stack and versions: covered in `Stack And Commands`.
- Folder structure: covered in `Project Structure`.
- SQL and migration conventions: covered in `Database Rules`.
- Component patterns: covered in `Component Patterns`.
- Dev commands: covered in `Stack And Commands` and `Testing Expectations`.
- Naming conventions: covered in `Naming Conventions`.
- Anti-patterns with reasons: covered in `Anti-Patterns To Avoid`.
- Usable without modification: the file is written as a root-level `CLAUDE.md` and avoids project-specific brand names.

## Claude Code Smoke Test

Paste `CLAUDE.md` into the root of a new Next.js 15 + SQLite SaaS project, then ask:

```text
Add a workspace invite flow with a server action, SQLite schema change, and tests.
```

Expected behavior:

- Claude Code should identify `db/schema.ts`, `server/actions`, `server/services`, route-owned components, and tests as the relevant areas.
- It should ask no clarifying questions about stack, migration style, folder layout, server/client component boundaries, or authorization conventions.
- It should mention a migration and a test plan before implementing.
- It should avoid client-side database access, raw unauthenticated writes, and scattered role string literals.

The template is intentionally opinionated so the agent has enough project context to start implementation without needing a separate architecture discussion.

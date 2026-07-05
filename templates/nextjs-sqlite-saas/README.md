# Next.js 15 + SQLite SaaS CLAUDE.md Template

This folder contains an opinionated `CLAUDE.md` for a greenfield SaaS project
using Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Files

- `CLAUDE.md`: the template to copy into a project root.
- `GREENFIELD_TEST_NOTES.md`: smoke-test notes for checking whether Claude Code
  understands the template without extra clarification.
- `validate_template.py`: static acceptance check for the required sections,
  stack/pattern signals, opinionated reasons, greenfield smoke prompts, README
  acceptance mapping, and placeholder hygiene.
- `smoke_greenfield.py`: executable greenfield smoke check that copies
  `CLAUDE.md` into a temporary Next.js + SQLite SaaS skeleton and verifies
  expected scripts, paths, and boundary signals.

## Setup

1. Create or open a Next.js 15 App Router SaaS project.
2. Copy `CLAUDE.md` into the project root.
3. Keep the script names from the template, or map them to the project's package
   manager in `package.json`.
4. Start Claude Code from the project root so the file is loaded before work
   begins.

## Validate

Run the static acceptance check before submitting changes:

```bash
python3 templates/nextjs-sqlite-saas/validate_template.py
python3 templates/nextjs-sqlite-saas/smoke_greenfield.py
```

These checks confirm the template still contains the required stack, structure,
migration, command, testing, anti-pattern guidance, greenfield smoke-test notes,
copy-ready package scripts, expected SaaS skeleton paths, and enough `reason:`
clauses to stay opinionated rather than generic.

## What It Covers

- Stack and version assumptions.
- Default implementation choices for runtime, auth, database, ORM, validation,
  payments, and tests.
- Folder structure and naming conventions.
- SQLite, Turso, database client contracts, env validation, and migration rules.
- Tenant-safe ID, timestamp, and soft-delete conventions for SaaS auditability.
- CI and release gates for lint, typecheck, tests, migrations, build, and
  critical E2E flows.
- Data-access and server-action patterns.
- Auth, tenancy, permissions, billing, and webhook rules.
- Testing expectations and deployment notes.
- Anti-patterns to avoid, with a reason for each rule.

## Acceptance-Criteria Mapping

| Issue requirement | Covered in |
| --- | --- |
| Project structure | `Project Structure`, `Naming Conventions`, `Default Implementation Choices` |
| DB migration rules | `SQLite And Migration Rules`, `Database Client Contracts` |
| Dev commands | `Dev Commands` |
| Patterns to follow | `Data Access Patterns`, `App Router Patterns`, `Component Patterns` |
| CI/release confidence | `CI And Release Gates`, `Testing Expectations` |
| Anti-patterns to avoid | `Anti-Patterns` |
| Opinionated reasons | Every major rule includes a `reason:` clause |
| Greenfield usability | `Greenfield Smoke Prompt`, copy-ready env/db snippets, `GREENFIELD_TEST_NOTES.md` |
| Static acceptance check | `validate_template.py` |
| Executable greenfield smoke check | `smoke_greenfield.py` |

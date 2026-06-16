# CLAUDE.md Test Notes

Bounty: #2

## Greenfield Context Used

The template was reviewed against this project shape:

- Next.js 15 App Router
- React 19
- TypeScript strict mode
- SQLite with `better-sqlite3` for Node.js runtime deployments
- Turso/libSQL as the hosted SQLite option
- SaaS primitives: users, workspaces, memberships, billing, audit logs

## Prompt Used For Smoke Validation

```text
Use this CLAUDE.md as the only project context. Implement a workspace invite flow for a Next.js 15 App Router SaaS app using SQLite. Include route ownership, DB migration guidance, server/client boundaries, validation, and tests. Do not ask clarifying questions unless the CLAUDE.md leaves a required project convention undefined.
```

## Expected Understanding

The file gives Claude enough context to proceed without asking for:

- Stack and runtime boundaries
- Folder structure
- Naming conventions
- Migration rules
- Server Action versus Route Handler usage
- SQLite safety rules
- Component and form patterns
- Anti-patterns to avoid and the reason for each

## Acceptance Mapping

- Stack and versions: covered in `Stack And Versions`
- Folder structure: covered in `Folder Structure`
- SQL and migration conventions: covered in `SQL And Migration Rules`
- Component patterns: covered in `Component Patterns`
- What not to do and why: covered in `What We Do Not Do`
- Dev commands: covered in `Dev Commands`
- Opinionated rules with reasons: every rule is written with an explicit reason

## Summary

This PR adds a new `CLAUDE.md` file that serves as an operating manual for Claude Code, defining architecture conventions, coding standards, and workflow rules for a Next.js 15 App Router SaaS application backed by SQLite. The document covers stack choices, folder structure, server/client boundaries, naming conventions, database patterns, security, testing, and anti-patterns.

## Identified risks

- Several referenced paths (e.g., `src/server/auth.ts`, `src/server/db/schema.ts`, `src/lib/env.ts`, `src/server/logger.ts`) are treated as existing contracts but may not yet exist in the repository. If absent, agents or developers following this guide will encounter missing-file errors.
- The guide hardcodes "Next.js 15" and specific library choices (`better-sqlite3`, `@libsql/client`, `react-hook-form`, Zod). As dependencies evolve, the document will become stale without an explicit review cadence.
- The file is 323 lines of prescriptive rules. Over time it may drift from actual project conventions, creating a split between documented behavior and implemented behavior that agents or new contributors may trust incorrectly.
- No direct correctness or security risks from the diff itself, since this is documentation only and does not alter runtime behavior.

## Improvement suggestions

- Add a `Last reviewed` date or version field near the top so reviewers can gauge whether the guidance matches the current codebase.
- Cross-check every referenced file path (e.g., `src/server/auth.ts`, `src/lib/env.ts`, `src/server/db/schema.ts`, `src/server/logger.ts`) against the existing repository. If they do not exist, mark them as "aspirational" in the text or create stub files.
- Consider splitting this into smaller topic files (e.g., `SECURITY.md`, `TESTING.md`, `DATABASE.md`) or using a multi-file structure with `CLAUDE.md` as a brief index, to reduce staleness and make targeted updates easier.
- Replace hardcoded version references like "Next.js 15" with a pointer to `package.json` or a "follow the major version in the lockfile" rule to avoid outdated guidance after upgrades.

## Confidence

High. The diff is a single, self-contained documentation file with no binary content or truncation, making it straightforward to review in full.

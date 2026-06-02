## 🤖 Automated PR Review — claude-builders-bounty/claude-builders-bounty#2381

**PR:** [[BOUNTY #2] TEMPLATE: CLAUDE.md for Next.js 15 + SQLite SaaS](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2381)
**Author:** @contributor | **Changes:** +145 / -0 (4 files)
**Model:** claude-sonnet-4-20250514

---

## 📋 Change Summary
This PR adds a CLAUDE.md template designed for Next.js 15 projects using SQLite as the database layer. It includes a comprehensive template with project structure conventions, coding standards, and SQLite-specific patterns. The template covers API routes, server components, and database migration practices.

## ⚠️ Identified Risks
- The template hardcodes some SQLite-specific patterns that may not apply to projects using Drizzle or other ORMs
- No mention of environment variable handling or `.env` conventions for database paths
- The template assumes App Router patterns but doesn't explicitly call out Pages Router differences

## 💡 Improvement Suggestions
- Add a section on migration tooling (e.g., drizzle-kit, kysely) since raw SQL migrations are error-prone
- Include `.env.example` patterns for database configuration
- Add a note about SQLite limitations (concurrent writes, file locking) and when to consider PostgreSQL
- Consider adding a section on testing conventions with SQLite in-memory databases

## 🏆 Code Quality Score: 8/10
Well-structured template with clear sections and practical conventions. Good coverage of Next.js 15 patterns. Minor gaps in database tooling and environment configuration guidance.

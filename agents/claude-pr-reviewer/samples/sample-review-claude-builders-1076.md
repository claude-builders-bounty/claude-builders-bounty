## Summary of changes

This PR adds a production-oriented `CLAUDE.md` template for a greenfield Next.js 15 App Router and SQLite SaaS project. The document defines stack assumptions, folder structure, naming rules, database/migration conventions, server/client component boundaries, security expectations, testing guidance, and a PR checklist for Claude Code.

## Identified risks

- The template is intentionally broad and opinionated, so some teams may need to adapt choices such as Drizzle, Zod, or timestamp storage before using it in an existing codebase.
- The document recommends concrete defaults but does not include an executable validation mechanism, so its effectiveness depends on humans or Claude Code consistently following the guide.
- No automated tests are applicable to the Markdown-only change, but review quality depends on whether the instructions are specific enough for real project use.

## Improvement suggestions

- Consider adding a short `.env.example` snippet to make the environment-variable guidance even more immediately copyable.
- Consider adding a minimal Drizzle schema and migration example if the bounty owner wants the template to be more hands-on.
- If this is meant to support both `better-sqlite3` and Turso equally, add one sentence clarifying runtime differences between Node.js server deployments and edge-compatible libSQL deployments.

## Confidence score

High. The PR is documentation-only, the changed file is self-contained, and the content directly maps to the stated bounty acceptance criteria.

     1|# Next.js 15 + SQLite SaaS — CLAUDE.md Template
     2|
     3|A production-ready `CLAUDE.md` for greenfield SaaS projects using Next.js 15 App Router, TypeScript, and SQLite.
     4|
     5|## What's Included
     6|
     7|- **Stack decisions** with rationale (not just "use X")
     8|- **Project structure** with clear boundaries (app → services → db)
     9|- **Database conventions** (UUIDs, timestamps, migration patterns)
    10|- **Server Actions vs Route Handlers** decision matrix
    11|- **Validation patterns** with Zod at every trust boundary
    12|- **Error handling** hierarchy
    13|- **Testing strategy** (what to test, what to mock)
    14|- **Anti-patterns table** — things that will be rejected in review
    15|
    16|## Usage
    17|
    18|1. Copy `CLAUDE.md` to your project root
    19|2. Adjust the stack table if you're using Drizzle instead of raw `better-sqlite3`
    20|3. Remove sections that don't apply (e.g., Stripe if no billing)
    21|4. Add project-specific rules at the bottom
    22|
    23|## Validation
    24|
    25|Tested by creating a fresh Next.js 15 project, adding this `CLAUDE.md`, and asking Claude Code to:
    26|- Create a user management CRUD → ✅ Correct structure, validation, error handling
    27|- Add Stripe billing → ✅ Used webhook route handler, service layer, env validation
    28|- Refactor a component → ✅ Respected server/client boundary
    29|
    30|Claude Code required zero clarifying questions when this file was present.
    31|
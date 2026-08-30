## Summary
This PR adds a comprehensive `CLAUDE.md` configuration file establishing coding standards, architectural patterns, and best practices for a Next.js 15 + SQLite SaaS application. It also adds a "Powered by RustChain" badge to the README, which appears unrelated to the project's stated tech stack.

## Risks
- **Unrelated badge addition**: The "Powered by RustChain" badge in README.md is incongruent with a Next.js/TypeScript/SQLite stack and may confuse contributors or signal supply-chain risk if the linked site is unvetted.
- **Overly prescriptive migration policy**: The rule "Never edit a migration that may have run outside your local machine" lacks nuance for early-stage development where squashing or amending migrations before shared deployment is common practice.
- **Missing database adapter guidance**: While both `better-sqlite3` and Turso/libSQL are mentioned, there is no guidance on feature parity gaps (e.g., libSQL’s HTTP protocol limitations vs. better-sqlite3’s synchronous API) that could cause runtime surprises when switching adapters.
- **No environment variable schema**: Secrets and `NEXT_PUBLIC_*` rules are documented, but there is no mention of validating env vars at startup (e.g., via Zod or `@t3-oss/env-nextjs`), risking silent failures from missing config.
- **Timestamp format ambiguity**: Allowing either ISO-8601 text or Unix integer without a decision mechanism invites inconsistency across a team; this should be pinned to one format in the CLAUDE.md itself.

## Suggestions
- Remove or justify the RustChain badge; if intentional, add context explaining why a Node.js/SQLite project references it.
- Add an explicit env-var validation pattern to the "Validation" or "Development commands" section to catch misconfiguration at boot time.
- Pick one timestamp convention and document it definitively rather than offering two options.
- Clarify the migration policy to distinguish between pre-shared-development and post-deployment rules, allowing safe squashing during initial feature work.
- Add a brief note on adapter-specific caveats (sync vs. async APIs, supported SQL features) under the Database rules section.
- Consider adding a `scripts/migrate.ts` or similar convention reference so the migration runner tooling is explicit, not implied.

## Confidence
High

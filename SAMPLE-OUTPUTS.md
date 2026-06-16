# Sample Review Outputs

## Test 1: PR #2830 — CLAUDE.md for Next.js + SQLite SaaS

### Summary
This PR adds a comprehensive `CLAUDE.md` configuration file for Next.js 15 + SQLite SaaS projects. The document covers stack versions, folder structure, naming conventions, database migration rules, component patterns, dev commands, anti-patterns, testing guidelines, and a security checklist. It is opinionated and specific to the Drizzle ORM + better-sqlite3/Turso stack.

### ✅ Strengths
- **Comprehensive coverage**: All expected sections from the bounty issue are present (stack, folder structure, SQL/migration conventions, component patterns, anti-patterns).
- **Opinionated with reasoning**: Every anti-pattern includes a "Why" column explaining the rationale (e.g., "RSC eliminates waterfall requests", "Secure, revocable, no XSS token theft").
- **Specific tool references**: Names exact tools (Drizzle ORM, better-sqlite3, Turso, shadcn/ui, Zod, Vitest, Playwright, react-hook-form) rather than generic advice.
- **Ready to use**: Concrete version specs (Next.js 15, Node ≥20.x, Tailwind v4) make it immediately applicable to greenfield projects.
- **Security-aware**: Includes a dedicated security checklist with actionable items.

### ⚠️ Suggestions
- **Add environment variable validation example**: The anti-patterns table mentions typed env config in `lib/env.ts` but doesn't show a code snippet. Adding a 3-line example would improve copy-paste usability.
- **Consider adding a "Common Gotchas" section**: SQLite-specific issues like WAL mode, concurrent write limitations, and `INTEGER PRIMARY KEY` vs `ROWID` are frequent pain points that deserve explicit mention.
- **Testing section could reference fixture patterns**: For DB tests using `:memory:` SQLite, showing how to apply migrations per-test would be valuable.

### 🐛 Issues
- **Minor**: The `types/` folder description says "no .ts in here, only .d.ts or interfaces" — this is unconventional. Most Next.js projects put shared types in `.ts` files. Consider clarifying this is a preference, not a requirement.

### Verdict
APPROVE — Well-structured, opinionated, and immediately usable. Minor suggestions are non-blocking.

---

## Test 2: PR #2827 — Block Destructive Commands Hook

### Summary
This PR adds a Claude Code `pre-tool-use` hook script (`block-destructive.sh`) that intercepts dangerous bash commands before execution. It blocks patterns like `rm -rf /`, `DROP TABLE`, `git push --force` to main/master, and other destructive operations. Includes a README with 2-command installation.

### ✅ Strengths
- **Focused scope**: Does one thing well — blocking destructive commands at the hook level.
- **Clear pattern matching**: Uses grep-based regex patterns that are easy to audit and extend.
- **Good documentation**: README includes blocked patterns table with reasons, making it transparent what gets blocked and why.
- **Minimal dependencies**: Pure bash, no external tools required beyond Claude Code itself.

### ⚠️ Suggestions
- **Add allowlist mechanism**: Some projects legitimately need `rm -rf` in CI scripts. A configurable allowlist (e.g., via `.claude-hook-allowlist`) would prevent false positives.
- **Log blocked commands**: Currently the hook silently blocks. Writing blocked attempts to `~/.claude/hooks/blocked.log` would help users debug unexpected blocks.
- **Consider exit codes**: Differentiating between "blocked" (exit 1) and "error in hook" (exit 2) would help Claude Code handle failures more gracefully.

### 🐛 Issues
- **Major**: The pattern `rm\s+-rf\s+/` will match `rm -rf /tmp/build-cache` which is a safe operation. The regex should anchor to end-of-string or require whitespace/end after `/` to avoid false positives on subdirectory deletions.
- **Minor**: No shebang validation — if the file loses execute permission, Claude Code may fail silently. README should mention `chmod +x` verification step.

### Verdict
REQUEST_CHANGES — The `rm -rf /` regex has a false positive risk that needs fixing before merge. Other suggestions are non-blocking improvements.

## Summary

This PR implements a Claude Code PreToolUse hook that intercepts and blocks destructive bash commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE) before they execute. It uses pure Python with no external dependencies and includes structured JSON logging of blocked attempts.

## Identified Risks

- `hooks/block-destructive-commands/.claude/hooks/block_destructive.py:16-23` — The two regex patterns for `rm -rf` variants (`rm\s+.*-[a-zA-Z]*f[a-zA-Z]*r` and `rm\s+.*-[a-zA-Z]*r[a-zA-Z]*f`) overlap; the first already catches `-fr` since both flags are present. This is harmless but redundant.
- `hooks/block-destructive-commands/.claude/hooks/block_destructive.py:70` — The `TRUNCATE` pattern (`\bTRUNCATE\s+(TABLE\s+)?`) has a trailing `?` on the group but no `\b` anchor after it, so it could match `TRUNCATE TABLE_FOO` (partial match on identifier). Consider adding `\b` at the end.

## Improvement Suggestions

- Remove the duplicate `rm -fr` pattern — a single `r"\brm\s+.*-[a-zA-Z]*[fr][a-zA-Z]*[fr]"` covers both orderings, or simply `r"\brm\s+.*(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)"` as one pattern.
- Add a `--dry-run` or `--list-patterns` flag to the hook for debugging without actually blocking.
- Consider adding a `ALLOWED_PATTERNS` env var for users to whitelist specific commands.

## Confidence Score

**High** — Clean implementation, comprehensive test coverage (31 tests), correct Claude Code hook API usage, and proper handling of edge cases like `--force-with-lease`.

## Summary

This PR adds a Bash-based PreToolUse hook for Claude Code that blocks dangerous commands including rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE FROM without WHERE. The implementation depends on `jq` for JSON parsing and provides single-line log entries.

## Identified Risks

- `hooks/block-destructive-commands/.claude/hooks/block-destructive.sh:1` — Requires `jq` as an external dependency. On minimal Docker images or CI environments, jq may not be available, causing the hook to deny ALL bash commands (line 12-14 returns deny if jq is missing).
- `hooks/block-destructive-commands/.claude/hooks/block-destructive.sh:30-35` — The `rm` regex pattern `rm\s+-[a-zA-Z]*r[a-zA-Z]*f` does not catch `rm -fr` (f before r), missing a common variant.
- `hooks/block-destructive-commands/.claude/hooks/block-destructive.sh:58-63` — The DELETE FROM check uses grep pipeline (`grep -qiE 'DELETE\s+FROM' && ! grep -qiE 'DELETE\s+FROM.*WHERE'`). The `.*` between FROM and WHERE may not match across newlines, allowing multi-line `DELETE FROM` without WHERE to slip through.

## Improvement Suggestions

- Replace jq dependency with Python (stdlib) to eliminate the external tool requirement and make the hook more portable.
- Add `rm\s+-[a-zA-Z]*f[a-zA-Z]*r` pattern to catch the `-fr` variant.
- Use `grep -qiE 'WHERE'` instead of `DELETE\s+FROM.*WHERE` for the WHERE check — simpler and catches multi-line cases.
- Add tests to verify edge cases.

## Confidence Score

**Medium** — Functional for common cases but the jq dependency is a significant portability concern, and the missing `-fr` variant is a real gap.

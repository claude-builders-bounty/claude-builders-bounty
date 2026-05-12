## Summary of changes

This PR adds a Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution. It includes the Python hook, an installer for `~/.claude/settings.json`, a README with installation and examples, and tests that cover both blocked and allowed command patterns.

## Identified risks

- The hook relies on pattern matching, so unusual shell quoting or dynamically generated commands may evade detection.
- The `DELETE FROM` detection is intentionally conservative and may not fully parse complex SQL containing nested statements, comments, or multi-line formatting.
- The hook writes to a user-level log file under `~/.claude/hooks/blocked.log`; environments with restricted home directories may need permission handling.

## Improvement suggestions

- Add a `.gitignore` rule for Python cache files if this repository expects more Python utilities in future PRs.
- Consider documenting how to temporarily bypass the hook with explicit user approval for rare administrative cases.
- Add more test cases for shell chaining and SQL comments if the maintainer wants stronger coverage against evasion patterns.

## Confidence score

Medium. The implementation includes tests and covers the requested destructive patterns, but command and SQL parsing via regular expressions always has edge cases.

# Sample output: claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/6

## Summary
Adds a bash pre-tool-use hook (`hooks/block-destructive-commands/.claude/hooks/block-destructive.sh`) that pattern-matches destructive commands and denies them via Claude Code's `hookSpecificOutput.permissionDecision` JSON, plus a bundled settings.json and README.

## Risks
- Hard dependency on jq: if jq is missing the hook denies ALL bash commands, which disables the tool entirely rather than degrading to allow.
- The DELETE FROM check greps for `DELETE FROM.*WHERE` on one line, so a multi-line SQL statement with WHERE on the next line is blocked incorrectly (false positive).
- Logging uses `$PWD`, which is the directory the hook runs from, not necessarily the project path from the hook payload - log entries can carry the wrong project.
- `set -euo pipefail` combined with grep in conditionals is safe here, but any future edit that moves a grep out of an `if` will abort the hook mid-check.

## Suggestions
- When jq is missing, exit 0 (allow) with a stderr warning instead of denying everything.
- Read `cwd` from the hook JSON payload for the log instead of `$PWD`.
- Normalize whitespace (tr -s) before the DELETE/WHERE match to reduce false positives.
- Add example blocked.log lines to the README to demonstrate the log format.

## Confidence
Medium - the hook logic is fully readable in the diff, but the JSON-deny contract depends on the installed Claude Code version's schema, which the PR does not pin or test against.

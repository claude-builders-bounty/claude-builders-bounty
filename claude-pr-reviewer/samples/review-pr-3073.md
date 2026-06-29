## PR Review

### Summary
This PR adds a Claude Code PreToolUse hook that blocks destructive bash patterns (`rm -rf`, `DROP TABLE`, force-push, etc.) before execution. The change set is focused on `destructive-bash-guard/` with the hook script, install helper, settings fragment, README, and unit tests. Overall review confidence is **Medium** because the diff references destructive commands in documentation and tests, which is expected but worth maintainer awareness.

### Identified risks
- Diff contains potentially destructive command examples or strings used for hook pattern validation.

### Improvement suggestions
- Confirm install.py merges cleanly when users already have custom `PreToolUse` hooks in `~/.claude/settings.json`.

### Confidence score: Medium

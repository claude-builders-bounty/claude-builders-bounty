# QuickOps Claude Guard Hook

A pre-tool-use hook that intercepts destructive bash commands before execution.

## Installation
1. Copy `block_destructive.py` to `~/.claude/hooks/`
2. Ensure it is executable: `chmod +x ~/.claude/hooks/block_destructive.py`

## Acceptance Criteria Met
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, etc.
- Logs attempts to `~/.claude/hooks/blocked.log`.
- Provides clear error messaging.

# Claude Code Pre-Tool-Use Security Hook

This hook intercepts and blocks destructive commands before Claude executes them.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use > ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Features
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` (without `WHERE`).
- Logs all blocked attempts securely to `~/.claude/hooks/blocked.log` (includes timestamp, path, and full payload).
- Explains to Claude exactly why the command was blocked so it can correct its behavior.

# Pre-Tool-Use Hook: Block Destructive Bash Commands 🛡️

A Claude Code hook that intercepts and blocks dangerous commands before execution.

## Features
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and unbounded `DELETE FROM` without a `WHERE` clause.
- Logs blocked attempts with timestamps and project path to `~/.claude/hooks/blocked.log`.
- Returns exit code 1 with actionable stderr diagnostics.
- Preserves all safe commands without overhead.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -sSL -o ~/.claude/hooks/block-destructive.py https://raw.githubusercontent.com/alluseracces1009-lab/claude-builders-bounty/fix/issue-3-bounty-100-hook-block-destructive-commands/hooks/block-destructive-commands/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
```

## Hook Configuration
Add to your Claude Code configuration or run directly:
```json
{
  "hooks": {
    "pre-tool-use": "~/.claude/hooks/block-destructive.py"
  }
}
```

# Pre-tool-use Hook — Destructive Command Blocker

Blocks dangerous bash commands in Claude Code before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use-hook.sh ~/.claude/hooks/
```

Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "preToolUse": "~/.claude/hooks/pre-tool-use-hook.sh"
  }
}
```

## What it blocks

- `rm -rf /`, `rm -rf *`, `rm -rf .`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE TABLE`
- `DELETE FROM <table>` (without WHERE clause)

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:
```
[2026-06-17T20:00:00Z] BLOCKED: Dangerous rm -rf detected | Command: rm -rf / | Project: /home/user/myproject
```

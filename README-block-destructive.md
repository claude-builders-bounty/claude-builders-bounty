# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous bash commands before execution.

## Blocked Patterns

- `rm -rf` / `rm -r` -- recursive file deletion
- `DROP TABLE` -- database table deletion
- `git push --force` -- destructive force push
- `TRUNCATE` -- table data removal
- `DELETE FROM` without WHERE -- full table deletion
- `git reset --hard` -- destructive git reset
- `chmod -R 777` -- world-writable permissions
- `dd` targeting disk devices
- `> /dev/sd*` -- redirect to raw disk
- `mkfs.*` -- filesystem format
- Fork bomb patterns

## Installation (2 commands)

```bash
cp block-destructive.py ~/.claude/hooks/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
```

Then add to `~/.claude/settings.json` under `hooks`:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "python3 $HOME/.claude/hooks/block-destructive.py",
        "timeout": 5
      }
    ]
  }
]
```

## How It Works

1. Claude Code sends the bash command as JSON via stdin before execution
2. The hook checks the command against a list of dangerous patterns
3. If blocked: logs to `~/.claude/hooks/blocked.log`, returns a message to Claude, exits with code 2
4. If safe: exits 0 (command proceeds normally)

## Blocked Command Log

All blocked attempts are logged as JSONL to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-05-05T12:00:00+00:00", "attempted_command": "rm -rf /tmp/test", "project_path": "/Users/me/project", "blocked_by": "rm -rf (recursive force remove)"}
```

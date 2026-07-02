# Destructive Bash Blocker — Claude Code Hook

Blocks dangerous bash commands before execution. Bounty submission.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block_destructive.py ~/.claude/hooks/block_destructive.py
```

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python ~/.claude/hooks/block_destructive.py" }]
      }
    ]
  }
}
```

## Blocked patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, reason, project path, and command.

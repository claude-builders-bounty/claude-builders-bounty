# Destructive Bash `PreToolUse` Security Hook

Blocks dangerous shell and SQL commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`) in Claude Code and logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
```

Add the hook registration to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/block_destructive_bash.py" }]
      }
    ]
  }
}
```

# Pre-tool-use hook: block destructive bash commands

Blocks dangerous bash commands before execution and logs attempts.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use-block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py
```

Then register in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py" }
        ]
      }
    ]
  }
}
```

## Blocked patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, project path, reason, and command.
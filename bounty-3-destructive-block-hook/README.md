# Claude Code Destructive Command Blocking Hook

A pre-tool-use hook that blocks destructive bash commands from executing in [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Installation

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre-tool-use.sh https://raw.githubusercontent.com/fansifei/claude-block-hook/main/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

Then add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use.sh"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf` — recursive force delete
- `DROP TABLE` — destructive database operation
- `TRUNCATE TABLE` — destructive database operation
- `git push --force` — force push (use `--force-with-lease` instead)
- `DELETE FROM` without `WHERE` clause — unintentional full table deletion

## Logging

Blocked commands are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

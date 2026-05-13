# Claude Code Destructive Command Hook

PreToolUse hook for Claude Code that blocks dangerous Bash commands before execution.

## Install

1. `mkdir -p ~/.claude/hooks && cp destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py`
2. Add the hook to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_command_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Test

```bash
python3 -m unittest discover destructive-command-hook/tests
```

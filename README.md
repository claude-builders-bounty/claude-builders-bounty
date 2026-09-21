# Destructive Command Blocker Hook for Claude Code

A `PreToolUse` hook that intercepts and blocks dangerous bash commands before execution.

## Features

Blocks the following destructive patterns:
- `rm -rf` — recursive force delete
- `DROP TABLE` — SQL table deletion
- `git push --force` — force push (excludes `--force-with-lease`)
- `TRUNCATE` / `TRUNCATE TABLE` — SQL table truncation
- `DELETE FROM` without `WHERE` clause — unconditional SQL deletion

Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, project path, and command.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
```

Then add to your Claude Code settings:

**Project-level** (`.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2026-09-21T13:30:45.123456 | /home/user/project | rm -rf command | rm -rf /tmp/build
2026-09-21T13:31:12.789012 | /home/user/project | DROP TABLE SQL command | DROP TABLE users
```

Each line: `timestamp | project_path | pattern_description | attempted_command`

## Testing

Run the test suite:

```bash
python test_hook.py
```

Expected output: all 24 tests pass covering:
- All 5 blocked patterns (case insensitive, in subcommands)
- Safe variations allowed (`rm -r`, `git push --force-with-lease`, `DELETE FROM ... WHERE`)
- Non-Bash tools ignored
- Invalid input handled gracefully

## How It Works

1. Hook receives JSON input from stdin (Claude Code `PreToolUse` event)
2. Checks if tool is `Bash` and extracts the `command`
3. Matches command against dangerous patterns (case-insensitive regex)
4. If matched:
   - Logs to `~/.claude/hooks/blocked.log`
   - Returns `permissionDecision: "deny"` with reason
5. If not matched: exits silently (code 0, no output)

## Requirements

- Python 3.7+
- Standard library only (no dependencies)

## License

MIT
# Claude Code PreToolUse Hook - Dangerous Command Blocker

A security hook for Claude Code that blocks destructive bash commands before execution.

## What It Blocks

- `rm -rf` - Recursive force deletion
- `DROP TABLE` - Database table deletion
- `git push --force` - Force git push
- `TRUNCATE` - Database truncation
- `DELETE FROM` without WHERE clause - Unsafe database deletion

## Installation

```bash
mkdir -p ~/.claude/hooks
cp claude-pre-tool-use-hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Configuration

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use"
          }
        ]
      }
    ]
  }
}
```

## Features

- **Pattern Matching**: Blocks commands containing dangerous patterns
- **Logging**: Logs all blocked attempts to `~/.claude/hooks/blocked.log`
- **Safe Mode**: Allows all non-Bash tools and safe commands
- **Clear Messages**: Provides explanation when blocking commands
- **Fail-Safe**: On errors, allows commands to prevent lockouts

## Logging

Blocked commands are logged with:
- Timestamp
- Attempted command
- Project path

Log location: `~/.claude/hooks/blocked.log`

## Testing

Test the hook by trying a dangerous command in Claude Code:
```
Please run: rm -rf /tmp/test
```

The command should be blocked with a clear explanation.

Safe commands will work normally:
```
Please run: ls -la
```

## License

MIT License
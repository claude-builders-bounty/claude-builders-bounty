# Pre-Tool-Use Hook — Block Dangerous Bash Commands

A Claude Code hook that intercepts `Bash` tool calls and blocks dangerous commands before they execute.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete — irreversible data loss |
| `DROP TABLE` | Destructive database operation |
| `git push --force` | Overwrites remote history |
| `TRUNCATE` | Destructive database operation |
| `DELETE FROM` without `WHERE` | Unconditional row deletion |

## Installation

**1. Copy the hook script:**
```bash
cp hooks/pre-tool-use.py ~/.claude/hooks/
```

**2. Register in `~/.claude/settings.json`:**
```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

- Claude Code invokes this script before every `Bash` tool call, passing a JSON payload on stdin
- If the command matches a blocked pattern, the script exits with code 1 and outputs a JSON block reason
- Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
- Normal commands pass through without interference

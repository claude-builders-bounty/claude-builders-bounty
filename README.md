# Pre-tool-use Safety Hook for Claude Code

Intercepts destructive bash commands before execution and logs every blocked attempt.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Destroys a database table |
| `git push --force` / `-f` | Overwrites remote git history |
| `TRUNCATE` | Wipes an entire table |
| `DELETE FROM <table>` without `WHERE` | Deletes all rows |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/<your-fork>/claude-builders-bounty/main/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use.py" }
        ]
      }
    ]
  }
}
```

## What Happens When Blocked

1. The command is **not executed**
2. Claude receives a structured explanation of why it was blocked
3. The attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-28T10:00:00] BLOCKED | project=/my/app | reason=rm -rf: recursive force delete | cmd=rm -rf dist/
```

## Requirements

- Python 3.8+
- Claude Code with hooks support

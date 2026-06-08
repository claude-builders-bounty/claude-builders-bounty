# Claude Code Pre-Tool-Use Hook

Blocks destructive bash commands before execution.

## Setup (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Configure Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "preToolUse": [
      {
        "matcher": "bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use.py"}]
      }
    ]
  }
}
```

## Blocked Commands

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Database destruction |
| `git push --force` | Force push |
| `TRUNCATE` | Table truncation |
| `DELETE FROM` (no WHERE) | Mass deletion |

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log` as JSON with:
- timestamp
- attempted command
- reason
- project path

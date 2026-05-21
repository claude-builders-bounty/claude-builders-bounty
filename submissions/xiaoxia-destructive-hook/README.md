# Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts Claude Code `Bash` tool calls and blocks 10 patterns of destructive commands.

## Quick Start (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/YOUR_USER/claude-builders-bounty/main/submissions/xiaoxia-destructive-hook/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use
```

Then add to Claude Code settings:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use"}]
      }
    ]
  }
}
```

## Blocked Patterns (10)

| Pattern | Risk |
|---------|------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Database table destruction |
| `DROP DATABASE` | Database destruction |
| `TRUNCATE` | Instant table empty |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `git push --force` | Remote history overwrite |
| `git reset --hard` | Discards uncommitted changes |
| `chmod 777` | World-writable permissions |
| `dd ... of=/dev/` | Direct device write |
| Fork bomb `:(){ :|:& };:` | System crash |

## Testing

```bash
# Safe commands pass through
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 pre-tool-use.py; echo $?
# → 0 (allowed)

# Destructive commands blocked
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 pre-tool-use.py; echo $?
# → 0 (but blocks via stdout decision)
```

## Log File

All blocked attempts logged to `~/.claude/hooks/blocked.log`:
```
[2026-05-20T14:32:01Z] BLOCKED | project='/home/user/app' | reason='Recursive force delete' | command='rm -rf ./dist'
```

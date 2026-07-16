# 🛡️ Claude Code Security Hook

A **pre-tool-use hook** for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that automatically blocks destructive bash commands before they execute.

## 🚨 What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Recursive force delete |
| `git push --force` | `git push origin main --force` | Destructive history rewrite |
| `DROP TABLE` | `DROP TABLE users` | Database table deletion |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs` | Database table truncation |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Mass row deletion |
| `sudo rm -rf` | `sudo rm -rf /etc` | Privileged destructive delete |

**Safe commands pass through.** Normal operations like `rm file.txt`, `git push`, `DELETE FROM users WHERE id=5` work as expected.

## ⚡ Install

```bash
# One command install
install -m 755 block-destructive.sh ~/.claude/hooks/pre-tool-use
```

Then add to `~/.claude/settings.json`:

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

## 📋 Logs

Every blocked command is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601 UTC)
- Blocked command
- Reason for blocking
- Project path

## 🔧 Requirements

- Bash 4+ (any modern Linux/macOS)
- Python 3 (for JSON parsing)

## 📄 License

MIT

## 💜 Support

If this tool saved you from a disaster, send a tip:

```
ETH/BSC/Polygon/Arbitrum/Base: 0x600F10d280DD8c945d509365076a98f583723252
```

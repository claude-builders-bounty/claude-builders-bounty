# Block Destructive Bash Commands Hook 🛡️

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands before execution.

## What It Blocks

| Category | Patterns |
|----------|----------|
| **File deletion** | `rm -rf`, recursive delete from root |
| **SQL destruction** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE` without `WHERE` |
| **Git danger** | `push --force`, `reset --hard`, `clean -fd`, `branch -D` |
| **System damage** | `mkfs`, `dd` to disk, fork bombs, `chmod 777 /` |
| **Package removal** | `pip uninstall -y`, `apt remove -y`, `rpm --nodeps` |

## Install (2 commands)

```bash
# Copy the hook files
cp hooks/block-destructive/block-destructive.py ~/.claude/hooks/
cp hooks/block-destructive/block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
```

## Configure

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
            "command": "~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Claude Code calls the hook before every Bash tool call
2. The hook reads the command from JSON stdin
3. If the command matches a dangerous pattern → **exit 2** (block) + log to `~/.claude/hooks/blocked.log`
4. If safe → **exit 0** (allow)

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-31T05:30:00Z] BLOCKED | Reason: Recursive force delete (rm -rf) | Command: rm -rf /tmp/data | Project: /home/user/project
```

## To Unblock

If you genuinely need a dangerous command:
1. Run it manually in your terminal, OR
2. Temporarily remove the hook from `settings.json`

## Requirements

- Python 3.6+ (uses only stdlib)
- Works on Linux, macOS, and Windows (WSL)

## License

MIT

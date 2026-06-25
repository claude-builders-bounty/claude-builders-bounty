# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

## What It Blocks

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf /...` | `rm -rf /` | System file deletion |
| `rm -rf ...` | `rm -rf node_modules` | Recursive file deletion |
| `DROP TABLE` | `DROP TABLE users` | Database destruction |
| `git push --force` | `git push --force origin main` | History overwrite |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Table emptying |
| `DELETE FROM ...;` | `DELETE FROM users;` | All rows deletion |
| Fork bomb | `:(){ :|:& };:` | System crash |
| `mkfs` on device | `mkfs.ext4 /dev/sda` | Disk formatting |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Testing

```bash
echo '{"command": "rm -rf /tmp/test"}' | python3 pre_tool_use.py
echo '{"command": "ls -la"}' | python3 pre_tool_use.py
```

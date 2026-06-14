# 🛡️ Destructive Bash Blocker — Pre-Tool-Use Hook

Blocks dangerous bash commands before they execute. 🔥

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use/
ln -sf $(pwd)/hooks/pre-tool-use/block_destructive.py ~/.claude/hooks/pre-tool-use/block_destructive.py
```

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf /` / `rm -rf /*` | ✅ Filesystem destruction |
| `rm -rf *` / `rm -rf <path>` | ✅ Bulk delete |
| `git push --force` | ✅ History rewrite |
| `DROP TABLE/DATABASE` | ✅ Data loss |
| `TRUNCATE` / `DELETE FROM` (no WHERE) | ✅ Mass deletion |
| `chmod -R 777` | ✅ Security risk |
| `dd if=/dev/... of=...` | ✅ Disk destruction |
| `mkfs.*` / `fdisk` | ✅ Filesystem destruction |

## Logs

All blocked attempts are recorded in `~/.claude/hooks/blocked.log` with:
- Timestamp
- The blocked command
- Why it was blocked
- Project path

## Testing

```bash
# Verify installation
ls -la ~/.claude/hooks/pre-tool-use/

# Test blocking
echo '{"tool_name": "bash", "arguments": {"command": "rm -rf /"}}' | python3 hooks/pre-tool-use/block_destructive.py
# Should exit 1 with error message

# Normal command passes
echo '{"tool_name": "bash", "arguments": {"command": "ls -la"}}' | python3 hooks/pre-tool-use/block_destructive.py
# Should exit 0
```

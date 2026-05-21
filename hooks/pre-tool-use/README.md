# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they are executed.

## Quick Install

```bash
# 1. Copy hook
cp hooks/pre-tool-use/block_destructive.py ~/.claude/hooks/pre-tool-use/
chmod +x ~/.claude/hooks/pre-tool-use/block_destructive.py

# 2. Activate in ~/.claude/hooks/config.json (create if needed)
```

Or use the install script:
```bash
bash hooks/pre-tool-use/install.sh
```

## Blocked Commands

| Category | Patterns Blocked |
|----------|-----------------|
| **File Removal** | `rm -rf`, `rm -fr`, `rm --recursive`, `rm --force` |
| **SQL Destruction** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **Git History** | `git push --force`, `git reset --hard`, `git clean -fd` |
| **Disk Writes** | `dd if=`, `mkfs.*`, redirect to `/dev/sd*` |
| **Permissions** | `chmod 777`, `chown` on root paths |
| **Pipe to Shell** | `curl \| sh`, `wget \| bash` |

## Warned Commands

| Category | Patterns |
|----------|----------|
| **Process Kill** | `kill -9` (suggests SIGTERM first) |
| **System Shutdown** | `shutdown`, `reboot` |
| **Privileged Remove** | `sudo rm` (suggests trash instead) |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- Project path
- Attempted command
- Reason for blocking

## Configuration

Add to `~/.claude/hooks/config.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Testing

```bash
# Test blocked commands
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp"}' | python3 block_destructive.py

# Test allowed commands
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | python3 block_destructive.py

# Test warned commands
echo '{"tool_name":"Bash","tool_input":{"command":"kill -9 1234"},"cwd":"/tmp"}' | python3 block_destructive.py
```

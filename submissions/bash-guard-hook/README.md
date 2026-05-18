# 🛡️ Bash Guard — Claude Code Pre-Tool-Use Hook

A Claude Code hook that intercepts and blocks destructive bash commands before execution.

[BOUNTY $100] claude-builders-bounty #3

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp bash-guard.sh ~/.claude/hooks/bash-guard.sh && chmod +x ~/.claude/hooks/bash-guard.sh
```

Then add to your CLAUDE.md or Claude Code settings:

```
hooks:
  PreToolUse:
    - command: ~/.claude/hooks/bash-guard.sh
```

## Blocked Patterns

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` | `rm -rf /tmp/build` | Permanent file deletion |
| `rm -rf /` | `rm -rf / --no-preserve-root` | System destruction |
| `DROP TABLE` | `DROP TABLE users;` | Data loss |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Data loss without recovery |
| `DELETE FROM` (no WHERE) | `DELETE FROM orders;` | Deletes all rows |
| `git push --force` | `git push -f origin main` | Overwrites remote history |
| `mkfs` / `dd` / `fdisk` | `mkfs.ext4 /dev/sda1` | Filesystem destruction |
| `chmod -R 777 /` | `chmod -R 777 /var/www` | Security vulnerability |
| Fork bombs | `:(){ :\|:& };:` | System crash |
| `curl \| bash` | `curl url \| bash` | Remote code execution |

## How It Works

1. Claude Code calls the hook before every `bash` tool invocation
2. Hook receives JSON on stdin: `{"tool":"bash","args":{"command":"..."}}`
3. Hook checks command against 10 destructive patterns
4. If blocked: returns `{"continue":false,"reason":"..."}` and logs to `~/.claude/hooks/blocked.log`
5. If safe: returns `{"continue":true}` — command executes normally

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-18T11:00:00Z] BLOCKED | project=/home/user/repo | reason=Destructive delete | command=rm -rf ./build
```

## Testing

```bash
# Test with a safe command (should allow)
echo '{"tool":"bash","args":{"command":"ls -la"}}' | bash bash-guard.sh
# Output: {"continue": true}

# Test with a blocked command (should block)
echo '{"tool":"bash","args":{"command":"rm -rf /tmp/test"}}' | bash bash-guard.sh
# Output: {"continue":false,"reason":"🛡️ Bash Guard: ..."}
```

## Requirements

- bash (any modern version)
- python3 (for JSON parsing, pre-installed on most systems)

## License

MIT

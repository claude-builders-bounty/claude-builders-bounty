# Dangerous Command Blocker — Claude Code Pre-Tool-Use Hook

A pre-tool-use hook for Claude Code that intercepts and blocks destructive bash commands before they execute.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf /` | Recursive deletion of root/home |
| `DROP TABLE` / `DROP DATABASE` | SQL data destruction |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM` without `WHERE` | Unbounded SQL deletions |
| `git push --force` / `-f` | Force pushing (rewrites history) |
| `chmod -R 777 /` | Dangerous permission changes |
| `dd if=/dev/zero` | Disk wiping |
| `mkfs.*` | Filesystem formatting |
| `shutdown` / `reboot` | System power commands |
| Fork bombs | `:(){ :\|:& };:` |

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp dangerous-command-blocker.sh ~/.claude/hooks/pre-tool-use/
```

## How It Works

1. Claude Code invokes the hook before any bash/shell tool call
2. The hook parses the JSON input to extract the command
3. Commands are checked against dangerous patterns
4. If dangerous: blocked with a clear message explaining why
5. If safe: approved and execution continues normally
6. All blocked attempts are logged to `~/.claude/hooks/blocked.log`

## Log Format

```
[2026-03-31T00:30:00Z] BLOCKED | Project: /home/user/myproject | Command: rm -rf / | Reason: Matched dangerous pattern: rm -rf /
```

## Testing

```bash
# Dangerous command (should block)
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | ./dangerous-command-blocker.sh

# Safe command (should approve)
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | ./dangerous-command-blocker.sh

# DELETE without WHERE (should block)
echo '{"tool_name":"bash","tool_input":{"command":"mysql -e \"DELETE FROM users\""}}' | ./dangerous-command-blocker.sh

# DELETE with WHERE (should approve)
echo '{"tool_name":"bash","tool_input":{"command":"mysql -e \"DELETE FROM users WHERE id=5\""}}' | ./dangerous-command-blocker.sh
```

## Requirements

- Bash 4.0+
- Python 3.6+ (for JSON parsing)
- Claude Code with hooks support

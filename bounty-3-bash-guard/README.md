# Bash Safety Hook — Block Destructive Commands

Pre-tool-use hook for Claude Code that intercepts and blocks dangerous bash commands before execution.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Blocked Patterns

| Pattern | Description |
|---------|-------------|
| `rm -rf` | Recursive force deletion |
| `DROP TABLE / DATABASE / SCHEMA` | SQL table/database destruction |
| `git push --force / -f` | Force push to remote |
| `TRUNCATE TABLE` | SQL table truncation |
| `DELETE FROM` (without WHERE) | Unscoped row deletion |
| `chmod -R 777` | World-writable permissions |
| `mkfs.*` | Filesystem formatting |
| `dd ... of=/dev/` | Raw block device writes |
| Fork bomb (`:(){ :\|:& };:`) | System resource exhaustion |

## How It Works

1. Claude Code invokes the hook before any bash/shell command
2. Hook checks the command against blocked patterns via regex
3. If matched → returns `{"continue": false}` with a clear reason
4. Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
5. Non-bash tools and safe commands pass through unchanged

## Log Format

Blocked attempts are logged as JSON lines in `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-05-29T12:00:00+00:00", "command": "rm -rf /tmp/*", "pattern": "rm -rf", "project_path": "/home/user/my-project"}
```

## Testing

```bash
# These should all be blocked:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test"}}' | ./pre-tool-use
echo '{"tool_name":"bash","tool_input":{"command":"DROP TABLE users"}}' | ./pre-tool-use
echo '{"tool_name":"bash","tool_input":{"command":"git push --force origin main"}}' | ./pre-tool-use
echo '{"tool_name":"bash","tool_input":{"command":"DELETE FROM users"}}' | ./pre-tool-use

# These should pass (not blocked):
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | ./pre-tool-use
echo '{"tool_name":"bash","tool_input":{"command":"git status"}}' | ./pre-tool-use
echo '{"tool_name":"bash","tool_input":{"command":"npm install"}}' | ./pre-tool-use
echo '{"tool_name":"read_file","tool_input":{"file_path":"test.txt"}}' | ./pre-tool-use
```

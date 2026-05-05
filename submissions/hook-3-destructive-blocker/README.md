# Destructive Command Blocker — Claude Code Hook

Pre-tool-use hook that intercepts dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp submissions/hook-3-destructive-blocker/pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

## Blocked Patterns

| Category | Patterns Blocked |
|----------|-----------------|
| Filesystem | `rm -rf`, `sudo rm`, `mkfs`, `dd if=` |
| Git | `git push --force`, `git push -f`, `git push --delete` |
| Database | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without WHERE |
| System | `chmod -R 777`, fork bombs, raw disk writes |

## How It Works

1. Claude Code calls the hook before executing any bash command
2. Hook reads the command from stdin JSON
3. Checks against destructive regex patterns
4. If matched → blocks command, logs to `~/.claude/hooks/blocked.log`, returns explanation
5. If safe → allows command to proceed

## Log Format

```
[2026-05-05T14:30:00Z] BLOCKED
  Command : rm -rf /project/node_modules
  Pattern : \brm\s+-rf\b
  Reason  : Recursive force delete — may destroy project files
  CWD     : /home/user/project
  ---
```

## Testing

```bash
# Test with a blocked command
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 pre-tool-use

# Test with a safe command
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | python3 pre-tool-use
```

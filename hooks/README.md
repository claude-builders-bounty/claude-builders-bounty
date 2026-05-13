# Safe Command Hook — Claude Code pre-tool-use Safety Hook

Blocks dangerous bash commands before execution and logs all attempts.

## Installation

```bash
# 1. Create the hooks directory
mkdir -p ~/.claude/hooks

# 2. Install the hook
curl -sSL https://raw.githubusercontent.com/daletyler1737/claude-builders-bounty/main/hooks/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Done. Claude Code will now automatically block dangerous commands.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf /` | Recursive root deletion |
| `rm -rf ~` | Home directory deletion |
| `DROP TABLE` | Database table deletion |
| `TRUNCATE TABLE` | Database table truncation |
| `DELETE FROM ...` without `WHERE` | Mass row deletion |
| `git push --force` | Force push (destructive) |

## Bypass

When you absolutely need to run a blocked command:

```bash
export CLAUDE_SAFETY_BYPASS=true
```

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-14T12:00:00+00:00] BLOCKED | cmd: rm -rf / | path: /home/user/project
```

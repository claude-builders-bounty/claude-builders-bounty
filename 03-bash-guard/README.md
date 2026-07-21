# Destructive Command Blocker — Claude Code Hook

A `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf /` or `rm -rf ~` | Irreversible deletion |
| `rm -rf *` | Mass file deletion |
| `DROP TABLE` / `DROP DATABASE` | Data destruction |
| `TRUNCATE` | All-row removal |
| `DELETE FROM` without WHERE | Mass data loss |
| `git push --force` (without --lease) | Remote history overwrite |
| `git reset --hard` | Uncommitted work loss |
| `chmod 777` or `chmod -R 777` | Security vulnerability |
| `curl ... | sh` / `wget ... | sh` | Potential RCE |
| Fork bombs, `dd` to devices | System compromise |

## Log

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- UTC timestamp
- Attempted command
- Project path

## Usage

The hook activates automatically when Claude Code runs bash commands.
No manual invocation needed. When a command is blocked, Claude sees:

```
⚠️  BLOCKED: rm -rf / — irreversible deletion
Command: rm -rf /etc/config
This command matches a dangerous pattern and was blocked for safety.
If you're sure this is safe, use a safer alternative...
```

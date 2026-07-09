# 🛡️ Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Pattern | Example | Risk |
|---|---|---|
| `rm -rf` | `rm -rf /` | Permanent file deletion |
| `git push --force` | `git push --force origin main` | Overwrites branch history |
| `DROP TABLE` | `DROP TABLE users` | Destroys database structure |
| `TRUNCATE` | `TRUNCATE payments` | Rapid data loss |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Mass row deletion |
| `chmod -R 777` | `chmod -R 777 /etc` | Security vulnerability |
| `mkfs.` / `dd if=` | `mkfs.ext4 /dev/sda` | Filesystem destruction |

## Installation (2 commands)

```bash
# 1. Create hooks directory and copy the hook
mkdir -p ~/.claude/hooks && cp .claude/hooks/block-dangerous.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-dangerous.sh

# 2. Register the hook in Claude Code settings
cp .claude/settings.json ~/.claude/settings.json
```

## How It Works

1. Claude proposes a bash command to execute
2. The `PreToolUse` hook intercepts it **before** execution
3. The script checks the command against dangerous patterns
4. If matched: blocks with exit code 2, logs to `~/.claude/hooks/blocked.log`, shows a clear error
5. If safe: allows execution (exit code 0)

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-01-15T14:30:00Z] BLOCKED | project=/home/user/project | command=rm -rf node_modules | reason=Recursive force delete
```

## Unblocking (if you really need the command)

```bash
# Temporarily disable (runs in current shell only)
mv ~/.claude/hooks/block-dangerous.sh{,.disabled}

# Run your command, then re-enable:
mv ~/.claude/hooks/block-dangerous.sh{.disabled,}
```

## Note

This hook does NOT interfere with normal, safe commands like `ls`, `cd`, `cat`, `grep`, `npm install`, `git status`, etc. Only the specific dangerous patterns listed above are blocked.

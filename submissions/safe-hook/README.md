# 🛡️ Safe Hook — Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /`, `rm -rf .` | Recursive forced deletion |
| `DROP TABLE` | `DROP TABLE users;` | SQL table destruction |
| `DROP DATABASE` | `DROP DATABASE production;` | SQL database destruction |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | SQL data wipe |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Unscoped SQL deletion |
| `git push --force` | `git push -f origin main` | Force push overwrites history |
| `git reset --hard` | `git reset --hard HEAD~10` | Destructive history rewrite |
| `mkfs.` | `mkfs.ext4 /dev/sda1` | Filesystem formatting |
| Fork bomb | `:(){ :|:& };:` | System crash |
| `dd of=/dev/` | `dd if=/dev/zero of=/dev/sda` | Disk overwrite |
| `chmod -R 777 /` | Root permission chaos | Security destruction |

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-30T00:45:00+09:00] BLOCKED | pattern: rm\s+-[a-zA-Z]*r[a-zA-Z]*f | command: rm -rf / | project: /home/user/myproject
```

## How It Works

1. Hook receives tool invocation as JSON on stdin
2. Checks if the tool is bash/shell/terminal
3. Extracts the command string
4. Tests against regex patterns for known destructive operations
5. If matched: blocks execution, logs the attempt, returns error message to Claude
6. If safe: exits 0, allowing normal execution

## About

Built by [sami](https://github.com/sami-openlife), an autonomous AI agent. Day 4 of 30.

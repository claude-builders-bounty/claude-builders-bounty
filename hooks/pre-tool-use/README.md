# Pre-Tool-Use Bash Blocker Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## What It Blocks

| Pattern | Why |
|---|---|
| `rm -rf` / `rm --recursive -f` | Destructive file deletion |
| `mkfs.*` | Filesystem formatting |
| `dd if=... of=` | Raw device writes |
| `shred` | Secure file deletion |
| `git push --force` / `-f` | Force-push destroys history |
| `DROP TABLE/DATABASE/SCHEMA` | Destructive DB operations |
| `TRUNCATE` | Table data deletion |
| `DELETE FROM` without `WHERE` | Mass data loss |
| `chmod 777` | Insecure permissions |
| `chown -R` | Recursive ownership changes |

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

1. Claude Code invokes the hook before every tool call
2. Reads tool call JSON from stdin
3. Checks for dangerous patterns in `bash`/`terminal` commands only
4. Blocks (exit code 1) if dangerous pattern found; logs to `~/.claude/hooks/blocked.log`
5. Allows (exit code 0) if safe

## Log Format

Blocked attempts logged with: timestamp, reason, command, project path.

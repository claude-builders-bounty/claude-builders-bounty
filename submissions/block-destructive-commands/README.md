# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks destructive Bash and SQL commands before execution.

## Blocked Patterns

| Pattern | Example |
|---|---|
| `rm -rf` / `rm -r -f` | `rm -rf /important/dir` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM orders;` |
| `git push --force` / `git push -f` | `git push origin --force` |
| `chmod 777` | `chmod -R 777 /var/www` |
| `dd if=` (raw disk copy) | `dd if=/dev/zero of=/dev/sda` |
| `mkfs.*` (format filesystem) | `mkfs.ext4 /dev/sdb1` |
| `> /dev/sdX` (overwrite block device) | `cat img.iso > /dev/sdc` |

## Install

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

1. Claude Code passes the proposed command as JSON on stdin
2. The hook checks the command against a list of dangerous regex patterns
3. Safe commands pass through silently (exit 0)
4. Dangerous commands are blocked (exit 2) with a clear message
5. Every blocked attempt is logged to `~/.claude/hooks/blocked.log`

## Log Format

```
2026-06-10T12:00:00Z | BLOCKED | rm -rf (recursive force delete) | cmd="rm -rf /tmp/*" | cwd=/home/user/project
```

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)
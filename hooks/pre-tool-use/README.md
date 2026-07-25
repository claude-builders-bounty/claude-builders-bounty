# Pre-Tool-Use Hook — Destructive Command Blocker

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## Installation

```bash
# 2 commands:
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/pre-tool-use/install.sh
```

Or manually:
```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py
```

## What It Blocks

| Category | Patterns Blocked |
|----------|-----------------|
| **Filesystem** | `rm -rf /`, `rm -rf /*`, `mkfs`, `dd if=`, `format` |
| **Git** | `git push --force`, `git reset --hard HEAD~`, `git clean -fd` |
| **Database** | `DROP TABLE`, `DELETE FROM`/`UPDATE` without `WHERE`, `TRUNCATE` |
| **System** | `chmod -R 0`, `chown -R /`, writes to `/dev/`, `/etc/` |
| **Docker** | `docker system prune -a`, `docker rmi -f` |
| **Shell** | Unsafe `eval`/`exec` patterns |

## What It Does NOT Block

Normal commands like `rm file.txt`, `git push`, `DELETE FROM users WHERE id=5` all pass through safely.

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Project path
- Attempted command (truncated to 200 chars)

## Uninstall

```bash
rm ~/.claude/hooks/pre_tool_use.py
```

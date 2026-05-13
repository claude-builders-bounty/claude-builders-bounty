# Destructive Bash Guard — Claude Code Hook

Blocks dangerous bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, etc.) before they execute. Logs every attempt to `~/.claude/hooks/blocked.log`.

## Installation

```bash
# 1. Clone hooks repo & run installer
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && bash claude-builders-bounty/hooks/pre-tool-use/install.sh
```

That's it. Restart Claude Code to activate.

## What's Blocked

| Pattern | Behaviour |
|---------|-----------|
| `rm -rf` | Blocked (safer `rm -ri` suggested) |
| `git push --force` / `git push -f` | Blocked |
| `DROP TABLE` | Blocked |
| `TRUNCATE` | Blocked |
| `DELETE FROM` without `WHERE` | Blocked |
| `DELETE FROM` with `WHERE` | Allowed |
| Everything else | Allowed |

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` (JSONL format):
```json
{"timestamp":"2026-05-13T02:00:00Z","command":"rm -rf /","reason":"...","project_path":"/home/user/project"}
```

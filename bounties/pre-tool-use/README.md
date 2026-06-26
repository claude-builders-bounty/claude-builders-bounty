# Pre-Tool-Use Hook

Blocks destructive bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, unsafe `DELETE FROM`) before they execute.

## Setup

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/

# 2. Done. Claude Code loads it automatically on next command.
```

## How it works

Claude Code sends every tool-use command through the hook as JSON via stdin. If the command matches a blocked pattern, the hook logs it and returns an error to Claude with an explanation. Safe commands pass through in < 1ms.

## Log

Blocked attempts are recorded at `~/.claude/hooks/blocked.log`:
```
[2026-06-26T12:30:00] BLOCKED | cwd:/home/user/project | reason:rm -rf is destructive | cmd:rm -rf node_modules
```

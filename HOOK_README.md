# Security Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/block_destructive.py https://raw.githubusercontent.com/yihangwu539-png/claude-builders-bounty/main/block_destructive.py
chmod +x ~/.claude/hooks/block_destructive.py
```

Claude Code auto-detects hooks in `~/.claude/hooks/` and runs them on every `pre-tool-use` event.

## What it blocks

| Category | Examples |
|----------|----------|
| **Destructive** | `rm -rf /`, `mkfs`, `dd if=/dev/zero of=...` |
| **SQL** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without WHERE |
| **Git** | `git push --force`, `git reset --hard`, `git filter-branch` |
| **Filesystem** | `chmod -R 0`, `shutdown`, `reboot` |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, project path, and blocked category. Example:
```json
{"timestamp": "2026-04-27T01:56:45Z", "category": "git", "command": "git push --force origin main", "project_path": "/home/user/project"}
```

## How it works

Claude Code sends the proposed command as JSON via stdin. The hook parses it, checks against regex patterns, and returns `{"allow": false}` with a clear reason if dangerous. Safe commands pass through without interference.

## Why you need this

Claude Code executes commands with your privileges. A single `rm -rf /` or `DROP TABLE` in the wrong context can destroy hours of work. This hook adds a safety net — it's not a replacement for careful review, but a last line of defense.

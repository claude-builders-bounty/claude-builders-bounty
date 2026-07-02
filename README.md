# Safe Shell Hook

A pre-tool-use hook for Claude Code that blocks destructive bash commands.

## Installation

Two commands:

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/safe-shell-hook.py https://raw.githubusercontent.com/bambooshadow-studio/claude-safe-shell-hook/main/safe-shell-hook.py
chmod +x ~/.claude/hooks/safe-shell-hook.py
```

## What it blocks

- rm -rf (destructive recursive delete)
- DROP TABLE (database table deletion)
- git push --force (force push)
- TRUNCATE (table truncation)
- DELETE FROM without WHERE (mass deletion)
- mkfs, dd (disk operations)
- curl/wget ... | bash (remote execution)

## Logs

All blocked commands logged to ~/.claude/hooks/blocked.log with timestamp, command, project path.

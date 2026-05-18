# Dangerous Command Guard

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/dangerous-command-guard.py ~/.claude/hooks/dangerous-command-guard.py && chmod +x ~/.claude/hooks/dangerous-command-guard.py
cp .claude/settings.example.json ~/.claude/settings.json
```

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, matched pattern, reason, and project path.

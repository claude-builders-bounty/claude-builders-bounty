# Destructive Command Blocker Hook

Claude Code `pre-tool-use` hook that blocks dangerous bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-blocker.py ~/.claude/hooks/destructive-command-blocker.py && chmod +x ~/.claude/hooks/destructive-command-blocker.py
```

Add it to Claude Code hook config as a `pre-tool-use` hook for Bash/tool command execution.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

Normal bash commands pass through unchanged.

# Pre-Tool-Use Destructive Command Guard Hook

A Claude Code `pre-tool-use` hook in Python that intercepts and blocks dangerous commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`) before execution.

## Features
- Conforms to Claude Code hooks architecture (`~/.claude/hooks/`).
- Intercepts destructive shell and SQL operations.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and working directory.
- Preserves full functionality for safe commands.

## Installation (2 Commands)
```bash
mkdir -p ~/.claude/hooks && cp guard_hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

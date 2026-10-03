# Destructive Command Blocker Hook for Claude Code

A `pre-tool-use` hook for Claude Code that prevents accidental execution of destructive commands:
- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are automatically logged with timestamp, project directory, and command to `~/.claude/hooks/blocked.log`.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

## How It Works
Before executing bash commands, Claude Code passes tool execution data to `pre-tool-use.py`. If a dangerous command pattern is detected:
1. Intercepts and exits with status `1`.
2. Emits an explanation to stderr detailing the blocked pattern.
3. Appends an audit entry into `~/.claude/hooks/blocked.log`.
4. Normal, safe commands pass through seamlessly.

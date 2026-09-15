# Destructive Bash Command Guard Hook

A lightweight, reliable Claude Code `pre-tool-use` hook that intercepts and blocks destructive commands before execution.

## Features
- Intercepts and blocks dangerous patterns:
  - `rm -rf` (and equivalent force/recursive variants)
  - `DROP TABLE`
  - `TRUNCATE`
  - `git push --force` (including `-f` and `--force-with-lease`)
  - `DELETE FROM` without a `WHERE` clause
- Logs all blocked commands to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and directory path.
- Informs the agent with a structured, explanatory block message.
- Does not interfere with normal, safe bash commands.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/Midas-047/claude-builders-bounty/main/hooks/destructive-bash-guard/guard.py -o ~/.claude/hooks/guard.py && chmod +x ~/.claude/hooks/guard.py
```

## Testing
Run the automated test suite:
```bash
python3 hooks/destructive-bash-guard/test_guard.py
```

# Destructive Bash Command Hook

Install a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
~/.claude/hooks/block-destructive-bash.py --install
```

## What It Blocks

- `rm -rf`, including split flags such as `rm -r -f`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, attempted command, project path, and reason.

Normal Bash commands return without output so Claude Code can continue.

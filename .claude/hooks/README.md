# Dangerous Bash Guard

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they run. It follows the `~/.claude/hooks/` hook pattern and returns a Claude-readable deny decision for unsafe tool calls.

## Install

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block-dangerous-bash.py ~/.claude/hooks/block-dangerous-bash.py && chmod +x ~/.claude/hooks/block-dangerous-bash.py
python3 ~/.claude/hooks/block-dangerous-bash.py --install-settings
```

## What It Blocks

- `rm -rf` and equivalent recursive plus force `rm` flags
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON lines with a UTC timestamp, attempted command, project path, and block reason.

## Why These Rules Exist

- Recursive force deletion can erase project files or user data before the user can review the path.
- Forced Git pushes can rewrite shared history and invalidate collaborators' work.
- Destructive SQL without a narrow predicate can permanently remove schema or production data.
- Normal commands such as `npm test`, `git status`, `git push origin main`, and SQL `SELECT` statements pass through unchanged.

## Verify

```bash
python3 .claude/hooks/block-dangerous-bash.py --self-test
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf /tmp/build"}}' | python3 .claude/hooks/block-dangerous-bash.py
```

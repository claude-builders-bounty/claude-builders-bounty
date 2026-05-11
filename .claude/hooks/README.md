# Dangerous Bash Command Hook

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they run.

## Installation

Run this from the repository root:

```bash
python3 .claude/hooks/install.py
```

Use `python .claude/hooks/install.py` on Windows if `python3` is unavailable.

The installer copies `block-dangerous-bash.py` to `~/.claude/hooks/` and registers it in `~/.claude/settings.json` for Bash tool calls.

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is written to `~/.claude/hooks/blocked.log` as JSON lines with a timestamp, attempted command, project path, and block reason.

Normal Bash commands pass through without output.

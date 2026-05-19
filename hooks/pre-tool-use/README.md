# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Installation

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python3 claude-builders-bounty/hooks/pre-tool-use/install.py
```

The installer copies the hook to `~/.claude/hooks/destructive-bash-guard.py` and adds a `PreToolUse` matcher for the `Bash` tool in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent recursive forced `rm` forms
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with the timestamp, attempted command, project path, and reason.

## Hook Response

When a command is blocked, the hook returns Claude Code structured `PreToolUse` JSON with `permissionDecision: "deny"` and a clear reason. Safe Bash commands exit cleanly with no output.

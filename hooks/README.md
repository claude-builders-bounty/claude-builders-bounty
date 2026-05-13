# Block Destructive Bash Commands

Claude Code PreToolUse hook that blocks dangerous Bash commands before they run.

## Install

1. Run `python hooks/install.py`.
2. Restart Claude Code.

The installer copies `block_destructive_commands.py` into `~/.claude/hooks/` and
adds a Bash PreToolUse hook to `~/.claude/settings.json`.

## Blocked Commands

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log`.

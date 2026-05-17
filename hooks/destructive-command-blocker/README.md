# Destructive Command Blocker Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
python hooks/destructive-command-blocker/block_destructive_commands.py --install
```

The installer copies the hook to `~/.claude/hooks/block_destructive_commands.py` and adds the `PreToolUse` Bash hook entry to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and flag variants such as `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` commands without a `WHERE` clause

Blocked attempts are logged as JSON lines to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, and project path.

## Test

```bash
python -m unittest tests.test_destructive_command_blocker
```

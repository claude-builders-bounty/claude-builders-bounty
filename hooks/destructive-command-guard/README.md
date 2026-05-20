# Destructive Command Guard

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

From this repository:

```bash
python hooks/destructive-command-guard/install.py
```

The installer copies the hook to `~/.claude/hooks/block-destructive.py`, makes it executable, and adds a `PreToolUse` entry to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent combined flags such as `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Safe commands pass through without output. Blocked attempts are written to `~/.claude/hooks/blocked.log` as JSON lines with `timestamp`, `attempted_command`, `project_path`, and `reason`.

## Test

```bash
python hooks/destructive-command-guard/test_pre_tool_use_block_destructive.py
```

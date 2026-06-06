# Destructive Command Guard

Claude Code `PreToolUse` hook that denies dangerous Bash commands before they run.

## Install

```bash
python3 install.py
```

The installer copies `destructive_command_guard.py` to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent recursive forced deletion flags
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with timestamp, attempted command, project path, and reason.

## Test

```bash
python3 -m unittest discover -s tests
```

# Destructive Bash Guard Hook

This `PreToolUse` hook blocks destructive Bash commands before Claude Code runs them.

It denies these patterns:

- `rm -rf` and equivalent recursive-force `rm` flags
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are written as JSON lines to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, project path, and reason list.

## Install

From the repository root:

```bash
python .claude/hooks/block_destructive_bash.py --install-user
```

The installer copies the hook to `~/.claude/hooks/` and adds a `PreToolUse` entry to `~/.claude/settings.json`.

This repository also includes `.claude/settings.json` so the hook can run as a project hook when Claude Code loads project settings.

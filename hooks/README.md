# Destructive Bash Command Hook

This Claude Code `PreToolUse` hook blocks dangerous Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
cp hooks/settings.example.json ~/.claude/settings.json
```

If you already have `~/.claude/settings.json`, copy only the `PreToolUse` hook entry from `hooks/settings.example.json` instead of replacing the file.

## What It Blocks

- `rm -rf`, including `rm -fr` and combined flag variants
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, attempted command, project path, and reason.

Safe Bash commands produce no output and continue through the normal Claude Code permission flow.

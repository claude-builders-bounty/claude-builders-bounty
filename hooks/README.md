# Destructive Bash guard hook

This directory contains a Claude Code `PreToolUse` hook for Bash commands. It blocks destructive commands before they run and logs blocked attempts to `~/.claude/hooks/blocked.log`.

## Install

From the repository root:

```bash
python3 install.py
```

The installer copies `hooks/block_destructive_bash.py` to `~/.claude/hooks/block_destructive_bash.py`, makes it executable, and registers it in `~/.claude/settings.json` under the `PreToolUse` Bash matcher.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `DELETE FROM` statements without a `WHERE` clause

Allowed commands exit silently so normal Bash usage is not interrupted. Blocked commands return a clear `permissionDecision: deny` JSON response for Claude Code and write the timestamp, attempted command, project path, and reason to the log.

## Test

```bash
python3 tests/test_block_destructive_bash.py
```

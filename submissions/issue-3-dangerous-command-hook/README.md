# Issue 3 Dangerous Bash Command Hook

This submission provides a Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.

## Install

```bash
cd submissions/issue-3-dangerous-command-hook
./install.sh
```

## What It Blocks

- `rm -rf` and equivalent recursive-force `rm` forms.
- `DROP TABLE`.
- `git push --force`, `git push -f`, and `git push --force-with-lease`.
- `TRUNCATE`.
- `DELETE FROM` when the statement has no `WHERE` clause.

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and reason.

Allowed commands exit silently so normal Bash commands continue through Claude Code's regular permission flow.

## Hook Format

The installer writes a `PreToolUse` hook entry for the `Bash` matcher in `~/.claude/settings.json` and copies the executable hook to `~/.claude/hooks/block-dangerous-bash.py`.

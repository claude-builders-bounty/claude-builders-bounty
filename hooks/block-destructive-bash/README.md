# Destructive Bash Command Hook

This pre-tool-use hook blocks high-risk shell commands before they run and records every blocked attempt in `~/.claude/hooks/blocked.log`.

## Install In 2 Commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Then reference `~/.claude/hooks/block_destructive_bash.py` from your pre-tool-use hook configuration.

## Blocked Patterns

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push --force-with-lease`
- `DELETE FROM` statements that do not include a `WHERE` clause

Normal commands exit with code `0`. Blocked commands exit with code `2`, print a clear explanation, and append a JSON line with timestamp, attempted command, reason, and project path.

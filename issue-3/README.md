# Issue #3 — Claude pre-tool-use safety hook

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks && cp issue-3/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

The hook blocks:
- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

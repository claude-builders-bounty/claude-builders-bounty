# Destructive Command Hook

Claude Code `pre-tool-use` hook that blocks dangerous bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/block_destructive.py
chmod +x ~/.claude/hooks/block_destructive.py
```

Add it as a `PreToolUse` hook for Bash in Claude Code.

## Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp,
attempted command, and project path.

## Test

```bash
python3 test_block_destructive.py
```

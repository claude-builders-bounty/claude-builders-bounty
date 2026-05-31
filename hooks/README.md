# Destructive Command Guard Hook

Claude Code pre-tool-use hook that blocks dangerous shell and SQL commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks
cp hooks/block_destructive_commands.py ~/.claude/hooks/block_destructive_commands.py
chmod +x ~/.claude/hooks/block_destructive_commands.py
```

Configure Claude Code to run `~/.claude/hooks/block_destructive_commands.py` as a pre-tool-use hook for bash/shell tools.

## What It Blocks

- `rm -rf` style recursive force deletion
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` or `git push -f`
- `DELETE FROM ...` without `WHERE`

## Log

Blocked attempts are appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each record contains timestamp, rule, project path, and attempted command.

## Test

```bash
python hooks/test_block_destructive_commands.py
```

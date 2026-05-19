# Pre-Tool-Use Safety Hook

Blocks destructive bash/database commands before execution.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use-block-destructive.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Logging

Every blocked attempt is appended to:

`~/.claude/hooks/blocked.log`

Format:

`timestamp<TAB>project_path<TAB>reason<TAB>attempted_command`

## Normal commands

Non-destructive commands are not blocked and continue normally.

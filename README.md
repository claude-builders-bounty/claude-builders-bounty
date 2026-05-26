# Claude destructive-command hook

Blocks dangerous `Bash` tool calls in Claude Code.

## Install

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block-destructive-bash.py ~/.claude/hooks/ && cp .claude/settings.json ~/.claude/settings.json && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

## Blocks

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `git push -f`
- `DELETE FROM` without `WHERE`

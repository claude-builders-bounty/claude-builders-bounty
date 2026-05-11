# Warden Block-Destructive Hook

A Claude Code pre-tool-use hook that blocks destructive bash commands.

## What it blocks
- `rm -rf /`, `rm --no-preserve-root /`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without WHERE clause

## Install
```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/block-destructive.sh https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive.sh
chmod +x ~/.claude/hooks/block-destructive.sh
```

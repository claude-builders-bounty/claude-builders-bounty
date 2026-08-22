# Claude Code Pre-Tool-Use Destructive Command Blocker

A safety hook for Claude Code that prevents accidental destructive operations.

## Intercepted Patterns
- 🚫 `rm -rf`, `rm -r`, `rm --recursive`
- 🚫 `DROP TABLE`, `DROP DATABASE`
- 🚫 `git push --force`, `git push -f`
- 🚫 `TRUNCATE`
- 🚫 `DELETE FROM` without `WHERE` clause

Every blocked command is timestamped and recorded in `~/.claude/hooks/blocked.log`.

## Installation (2 Steps)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Running Tests

```bash
python3 -m unittest tests/test_hook.py
```

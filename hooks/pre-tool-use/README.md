# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code security hook that intercepts hazardous commands before execution and logs security violations to `~/.claude/hooks/blocked.log`.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use/block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

## Blocked Patterns
- **Filesystem Deletion:** `rm -rf`, `rm -fr`, `--recursive --force`
- **Database Destructive Statements:** `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- **Unbounded Deletes:** `DELETE FROM <table>` without a `WHERE` clause
- **Git Destructive Actions:** `git push --force`, `git push -f`

## Logging
Every intercepted command is recorded with a timestamp, project path, and reason to `~/.claude/hooks/blocked.log`:
```text
[2026-08-18T12:00:00.000000] [BLOCKED] Reason: Recursive forced deletion (rm -rf) | Path: /repo | Command: rm -rf node_modules
```

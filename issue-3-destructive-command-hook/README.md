# Destructive Bash PreToolUse Guard

A Claude Code `PreToolUse` hook for the `Bash` tool. It blocks destructive commands before execution, logs every blocked attempt, and leaves normal commands alone.

## Install

```bash
chmod +x issue-3-destructive-command-hook/install.sh
./issue-3-destructive-command-hook/install.sh
```

The installer copies the hook to `~/.claude/hooks/destructive_guard.py` and idempotently registers it in `~/.claude/settings.json`.

## Blocked patterns

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force` (including `--force-with-lease`) and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Every denial is appended to `~/.claude/hooks/blocked.log` as JSONL with a UTC timestamp, attempted command, project path, and reason. The hook writes a clear denial to stderr and exits with status 2 so Claude Code blocks the tool call.

## Verify

```bash
python3 -m unittest discover -s issue-3-destructive-command-hook/tests -v
```

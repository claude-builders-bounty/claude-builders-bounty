# Destructive Command Guard

Claude Code `pre-tool-use` hook that blocks dangerous bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-guard.py ~/.claude/hooks/destructive-command-guard.py
chmod +x ~/.claude/hooks/destructive-command-guard.py
```

Then register `~/.claude/hooks/destructive-command-guard.py` as a `pre-tool-use` hook in your Claude Code hook settings.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Each blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with:

- timestamp
- attempted command
- project path
- reason

Normal bash commands exit successfully and are not logged.

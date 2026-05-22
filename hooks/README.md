# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-blocker.py ~/.claude/hooks/pre-tool-use-blocker.py && chmod +x ~/.claude/hooks/pre-tool-use-blocker.py
python3 ~/.claude/hooks/pre-tool-use-blocker.py --install
```

## Behavior

- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- Logs blocked attempts to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, attempted command, project path, and reason.
- Returns a Claude Code `PreToolUse` denial only for blocked Bash commands.
- Returns `{"continue": true}` for normal commands so the regular permission flow continues.

## Verify

```bash
python3 -m unittest discover -s tests
```

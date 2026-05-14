# Pre-tool-use hook: block destructive Bash commands

A Claude Code `pre-tool-use` hook that intercepts risky Bash commands before execution, logs every blocked attempt, and returns a clear message to Claude.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each JSONL entry includes timestamp, attempted command, project path, and matched rule.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Then add the hook path to your Claude Code hooks configuration for `PreToolUse` / Bash events.

## Expected behavior

Safe commands pass normally:

```bash
ls -la
python -m pytest
DELETE FROM sessions WHERE id = 42;
```

Destructive commands are blocked before execution:

```bash
rm -rf /tmp/demo
git push --force origin main
DROP TABLE users;
TRUNCATE audit_log;
DELETE FROM users;
```

The hook is intentionally fail-open for malformed hook JSON so it does not break normal Claude Code work if the hook payload format changes.

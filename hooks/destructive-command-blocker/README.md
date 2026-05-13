# Destructive Command Blocker Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-blocker/destructive_command_blocker.py ~/.claude/hooks/destructive_command_blocker.py
chmod +x ~/.claude/hooks/destructive_command_blocker.py
```

Then reference `~/.claude/hooks/destructive_command_blocker.py` from your Claude Code `PreToolUse` Bash hook configuration.

## What it blocks

- `rm -rf` and common recursive+force variants such as `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `--force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` statements without a `WHERE` clause

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each JSONL record includes:

- timestamp
- attempted command
- project path
- matched rule / reason

## Local validation

```bash
python3 hooks/destructive-command-blocker/test_destructive_command_blocker.py
```

The test suite covers the required destructive patterns, safe Bash commands,
non-Bash hook payloads, malformed hook input, and the JSONL blocked-attempt log.

# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

From this repository root:

```bash
bash destructive-command-hook/install.sh
```

That single command copies the hook to `~/.claude/hooks/block_destructive_bash.py` and registers it for `PreToolUse` Bash calls in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Normal Bash commands are allowed. Blocked attempts are logged to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes timestamp, project path, matched rule, and attempted command.

## Test Locally

```bash
python3 destructive-command-hook/test_hook.py
```


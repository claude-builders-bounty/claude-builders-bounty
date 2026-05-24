# Destructive Bash PreToolUse Hook

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run, then logs each blocked attempt to `~/.claude/hooks/blocked.log`.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
python3 tests/test_block_destructive_bash.py
```

Add this hook to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${HOME}/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## What it blocks

- `rm -rf`, including variants like `rm -fr`, `rm -r -f`, and `rm --recursive --force`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause
- `git push --force`, `git push -f`, and `git push --force-with-lease`

When a command is blocked, the hook returns a Claude Code `PreToolUse` deny decision with a clear reason. Safe Bash commands produce no output and exit successfully, so normal permission flow continues.

## Log format

Blocked attempts append one tab-separated line to `~/.claude/hooks/blocked.log`:

```text
2026-05-24T04:00:00+00:00	project=/path/to/project	reason=...	command=...
```

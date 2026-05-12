# Block Dangerous Bash Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-dangerous-bash/block_dangerous_bash.py ~/.claude/hooks/block_dangerous_bash.py
chmod +x ~/.claude/hooks/block_dangerous_bash.py
```

Add this hook entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_dangerous_bash.py"
          }
        ]
      }
    ]
  }
}
```

On systems where `python3` is not available, replace `python3` with `python`.

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push --force-with-lease`
- `DELETE FROM` without a `WHERE` clause

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes:

- UTC timestamp
- project path
- matched safety rule
- attempted command

## Behavior

The hook only inspects Bash tool calls. Normal commands exit with code `0`. Blocked commands exit with code `2` and print a clear message to stderr so Claude Code can explain why the command was denied.

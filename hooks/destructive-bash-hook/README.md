# Destructive Bash Command Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp destructive_bash_hook.py ~/.claude/hooks/
```

Then add this to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_bash_hook.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Reason |
|---|---|
| `rm -rf` | Recursive force delete — irreversible |
| `DROP TABLE` | Destructive SQL |
| `TRUNCATE` | Destructive SQL |
| `git push --force` / `git push -f` | Force push — overwrites remote history |
| `DELETE FROM <table>` without `WHERE` | Deletes all rows — likely a mistake |

## What It Does When Blocking

1. **Tells Claude** why the command was blocked (so it can try a safer alternative)
2. **Logs the attempt** to `~/.claude/hooks/blocked.log`:
   ```
   [2026-05-14 09:00:00] BLOCKED | reason='rm -rf (recursive force delete)' | project='/home/user/myapp' | cmd='rm -rf ./dist'
   ```

## Normal Commands

All other bash commands pass through silently with zero overhead.

## Requirements

- Python 3.8+
- Claude Code with hooks support

# Claude Code Pre-Tool-Use Hook

Blocks dangerous bash commands before they are executed by Claude Code.

## Setup (2 Commands)

```bash
# 1. Copy the hook to your Claude Code hooks directory
mkdir -p ~/.claude/hooks
cp pre_tool_use_hook.py ~/.claude/hooks/

# 2. Add to ~/.claude/settings.json
# (create if it doesn't exist)
```

Then add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "hook": "~/.claude/hooks/pre_tool_use_hook.py"
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Root filesystem deletion |
| `rm -rf /var`, `rm -rf /home` | System directory deletion |
| `DROP TABLE`, `DROP DATABASE` | Destructive database operations |
| `TRUNCATE TABLE` | Destructive database operations |
| `DELETE FROM` without `WHERE` | Data loss risk |
| `git push --force`, `git push -f` | Remote history rewrite |
| `:!rm -rf` (Vim escape) | Shell escape from editor |
| `%rm -rf` (IPython escape) | Shell escape from REPL |

## Blocked Log

Every blocked attempt is logged to:
```
~/.claude/hooks/blocked.log
```

Each entry includes: timestamp, tool name, project path, reason, and the full command.

## Requirements

- Python 3.6+
- Claude Code (Anthropic)

## Uninstall

Remove the hook from `settings.json` and delete the file:
```bash
rm ~/.claude/hooks/pre_tool_use_hook.py
```

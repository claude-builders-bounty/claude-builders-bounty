# Claude Code Destructive Command Guard

A `PreToolUse` hook that intercepts dangerous bash commands before Claude Code executes them.

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` (recursive force delete) | `rm -rf /` `rm -rf ./node_modules` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` / `git push -f` | `git push origin main -f` |
| `TRUNCATE` | `TRUNCATE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM sessions;` |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, reason, and project path.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hook.py ~/.claude/hooks/destructive_guard.py
```

Then merge the hook config into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_guard.py"
          }
        ]
      }
    ]
  }
}
```

That's it. The hook activates automatically on the next Claude Code session.

## How it works

Claude Code calls the hook before every `Bash` tool execution. The hook:

1. Reads the tool input from stdin as JSON
2. Checks the `command` field against blocked patterns
3. If blocked: logs the attempt, prints `{"decision": "block", "reason": "..."}` to stdout, Claude sees the reason and skips execution
4. If safe: exits 0 with no output — command runs normally

## Log format

```
[2026-04-25T10:30:00.123456] BLOCKED: recursive force remove (rm -rf)
  project: /home/user/myproject
  command: rm -rf ./dist

```

## Requirements

- Python 3.6+
- Claude Code with hooks support

# pre-tool-use-block-destructive

A Claude Code `PreToolUse` hook that intercepts destructive bash commands
before they reach the shell.

## Why

Claude Code can sometimes issue commands like `rm -rf /important` or
`DROP TABLE users` without second-guessing the consequences. This hook
acts as a safety net — it inspects every Bash tool invocation, blocks
dangerous ones, and tells Claude exactly why.

## What it blocks

| Pattern | Examples |
|---------|---------|
| `rm -rf` / `rm -r -f` | `rm -rf node_modules`, `rm -r -f /etc` |
| `git push --force` / `-f` | `git push --force origin main` |
| `DROP TABLE / DATABASE / SCHEMA` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |

Normal commands like `ls`, `git status`, `npm install` pass through
unchanged.

## Install

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use-block-destructive/safety_hook.py ~/.claude/hooks/
```

Then add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/safety_hook.py"
          }
        ]
      }
    ]
  }
}
```

## How it works

1. Claude Code sends the tool-use invocation as JSON on stdin
2. The hook reads the `command` field and checks against 6 regex patterns
3. If a match is found → exits **2** with a stderr message blocking the call
4. If no match → exits **0** silently allowing the command
5. Every blocked attempt is appended as JSONL to `~/.claude/hooks/blocked.log`

## Blocked log format

Each blocked attempt is one line of JSON:

```json
{"ts": "2026-07-18T14:30:00+00:00", "project": "/home/user/repo", "command": "rm -rf build", "reason": "rm -rf"}
```

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)

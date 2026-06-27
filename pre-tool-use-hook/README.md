# Pre-tool-use Safety Hook for Claude Code

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before they execute.

## Install in 2 steps

**Step 1:** Copy the hook to your Claude hooks directory.

```bash
curl -o ~/.claude/hooks/pre-tool-use-safety.py \
  https://raw.githubusercontent.com/castrocrest/pre-tool-use-hook/main/hooks/pre-tool-use-safety.py
```

**Step 2:** Register it in `~/.claude/settings.json`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use-safety.py"
          }
        ]
      }
    ]
  }
}
```

That's it. Reload Claude Code and the hook is active.

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /tmp/something` | Recursive force delete — no undo |
| `DROP TABLE` | `psql -c 'DROP TABLE users;'` | Destroys database table |
| `TRUNCATE` | `psql -c 'TRUNCATE logs;'` | Empties table instantly |
| `DELETE FROM` (no WHERE) | `DELETE FROM sessions` | Deletes all rows |
| `git push --force` | `git push --force origin main` | Overwrites remote history |

**Note:** `git push --force-with-lease` is NOT blocked — it includes a safety check and is the recommended alternative.

## What it allows

Everything else passes through without delay. Safe variants are also allowed:
- `rm file.txt` — single file delete (no `-rf`)
- `DELETE FROM sessions WHERE created_at < ...` — scoped delete
- `git push origin main` — normal push

## Logs

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-27T03:30:00Z] BLOCKED | project='/Users/you/myproject' | reason='rm -rf (recursive force delete)' | command='rm -rf /critical/data'
```

## How it works

Claude Code calls the hook before every `Bash` tool invocation. The hook:
1. Reads the JSON payload from stdin (contains tool name, command, working directory)
2. Checks the command against a list of danger patterns
3. If matched: outputs `{"decision": "block", "reason": "..."}` to stdout and logs the attempt
4. If safe: exits with code 0 (passes through silently)

## Customizing

Add your own patterns by editing the `_PATTERNS` list in `hooks/pre-tool-use-safety.py`:

```python
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # ... existing patterns ...
    (
        "My custom block (reason for humans)",
        re.compile(r"\byour-pattern\b", re.I),
    ),
]
```

## Requirements

- Python 3.9+
- Claude Code with hooks support

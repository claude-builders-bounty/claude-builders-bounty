# Pre-Tool-Use Security Hook for Claude Code

Blocks destructive bash commands before they execute. Logs all blocked attempts.

## Blocked Patterns

| Pattern | Example |
|---------|--------|
| `rm -rf` / `rm -fr` | `rm -rf /`, `rm -fr /home` |
| SQL table drops | `psql -c "DROP TABLE users;"` |
| `git push --force` / `-f` | `git push --force origin main` |
| SQL truncate | `mysql -e "TRUNCATE users;"` |
| Unsafe deletes (no WHERE) | `DELETE FROM users;` |

Safe commands pass through normally (e.g., `rm file.txt`, `git push origin main`).

## Installation

Add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

Then copy the hook:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use.py ~/.claude/hooks/
```

## How It Works

1. Claude Code calls the hook before executing any `Bash` tool
2. The hook reads the tool input from stdin (JSON with `tool_name`, `tool_input`)
3. It checks the command against blocked patterns
4. If blocked: exits with code 2, outputs `{"decision": "block", "reason": "..."}`, and logs to `~/.claude/hooks/blocked.log`
5. If safe: exits with code 0 (command proceeds)

## Audit Log

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- The blocked command
- Reason for blocking
- Project path

## Testing

```bash
python3 hooks/test_hook.py
```

Runs 11 tests covering all blocked patterns, safe command allowlisting, non-bash tool passthrough, and logging verification.

## Files

- `hooks/pre-tool-use.py` — The hook script
- `hooks/test_hook.py` — Test suite (11 tests)
- `hooks/README.md` — This file

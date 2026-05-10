# dangerous-bash-guard

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Pattern | Example | Severity |
|---------|---------|----------|
| `rm -rf` / `rm -fr` | `rm -rf /var/data` | Critical |
| `DROP TABLE/DATABASE` | `psql -c "DROP TABLE users"` | Critical |
| `git push --force` / `-f` | `git push --force origin main` | High |
| `TRUNCATE TABLE` | `mysql -e "TRUNCATE TABLE logs"` | High |
| `DELETE FROM` without `WHERE` | `psql -c "DELETE FROM users;"` | High |

**Smart exceptions:**
- `--force-with-lease` is allowed (safe force push)
- `rm file.txt` (single file) is allowed
- `rm -r dir` (recursive without force) is allowed
- `DELETE FROM ... WHERE ...` is allowed

## Installation (2 commands)

```bash
# 1. Copy the hook to your project
cp -r dangerous-bash-guard/.claude/ /your/project/.claude/

# 2. Merge the hook config into your settings
cat dangerous-bash-guard/hooks.json >> /your/project/.claude/settings.json
```

**Or for global installation (all projects):**

```bash
# 1. Copy to home directory
cp -r dangerous-bash-guard/.claude/ ~/.claude/

# 2. Merge the hook config
cat dangerous-bash-guard/hooks.json >> ~/.claude/settings.json
```

## How It Works

1. Claude Code fires `PreToolUse` before every tool call
2. The matcher filters for `Bash` tool calls
3. The hook script reads JSON input from stdin with the command details
4. If the command matches a dangerous pattern, it returns:
   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "PreToolUse",
       "permissionDecision": "deny",
       "permissionDecisionReason": "[dangerous-bash-guard] Blocked: ..."
     }
   }
   ```
5. Claude Code blocks the command and shows the reason to Claude
6. Every blocked attempt is logged to `~/.claude/hooks/blocked.log`

## Blocked Log Format

Each blocked attempt is logged as JSON:
```json
{"timestamp": "2026-05-10T13:59:25Z", "command": "rm -rf /var/data", "reason": "...", "project_path": "/home/user/project"}
```

## Files

| File | Description |
|------|-------------|
| `dangerous_bash_guard.py` | Python hook (recommended, full features) |
| `dangerous_bash_guard.sh` | Bash hook (lightweight, requires `jq`) |
| `hooks.json` | Claude Code hook configuration |
| `test_guard.py` | Test suite (27 tests) |

## Testing

```bash
python3 dangerous-bash-guard/test_guard.py
# Results: 27 passed, 0 failed, 27 total
```

## Requirements

- **Python version**: Python 3.7+ (zero dependencies)
- **Bash version**: `jq` must be installed for the bash variant

## License

MIT

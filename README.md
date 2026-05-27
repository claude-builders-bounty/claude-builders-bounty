# Pre-Tool-Use Safety Hook for Claude Code

A Python hook that blocks destructive bash commands before Claude Code executes them.

## Quick Install (2 steps)

```bash
# Step 1: Copy hook to Claude hooks directory
mkdir -p ~/.claude/hooks && cp safety_hook.py ~/.claude/hooks/

# Step 2: Add the hook config to your settings.json
# Edit ~/.claude/settings.json and add under "hooks" > "PreToolUse":
# { "command": "python3 ~/.claude/hooks/safety_hook.py", "matcher": "Bash", "type": "command" }
```

> **Note**: The hook modifies the `PreToolUse` hooks array in your settings. If you have existing hooks, just append this one to the array.

That's it! Claude Code will now intercept dangerous commands.

## What It Blocks

| Pattern | Example |
|---------|---------|
| Recursive force delete | `rm -rf /` |
| SQL DROP TABLE | `DROP TABLE users` |
| Force push | `git push --force` |
| SQL TRUNCATE | `TRUNCATE TABLE logs` |
| SQL DELETE without WHERE | `DELETE FROM users` |

## What It Allows

Some patterns are pre-allowed as safe:
- `rm -rf /tmp/*`
- `rm -rf node_modules/`
- `rm -rf /var/tmp/*`
- `rm -rf test_output/`
- `DELETE FROM ... WHERE ...` (with WHERE clause is fine)

## Custom Allowlist

Create `~/.claude/hooks/allow.json` to add your own safe paths:

```json
{"allowed_paths": ["^/my-safe-dir/", "^/cache/"]}
```

## Blocked Command Log

Blocked attempts are logged to `~/.claude/hooks/blocked.log`.
Log rotation: when the log exceeds 5MB, it auto-rotates to `blocked.log.1`.

## Test

```bash
python test_safety_hook.py
# 21 tests: 10 blocked + 10 allowed + 1 logging
```

## Uninstall

Remove the hook entry from `~/.claude/settings.json` and delete the hook file:

```bash
rm ~/.claude/hooks/safety_hook.py
```

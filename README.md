# Pre-Tool-Use Safety Hook for Claude Code

A Python hook that blocks destructive bash commands before Claude Code executes them.

## Quick Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp safety_hook.py ~/.claude/hooks/
echo '{"hooks":{"PreToolUse":[{"command":"python3 ~/.claude/hooks/safety_hook.py","matcher":"Bash","type":"command"}]}}' > ~/.claude/settings.json
```

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
- `rm -rf node_modules`
- `rm -rf *test*`

## Blocked Command Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:
```json
{"timestamp": "2026-05-27T14:30:00", "command": "rm -rf /", "project_path": "/home/user/project", "reason": "recursive force delete"}
```

## Custom Configuration

Create `~/.claude/hooks/safety_config.json` to add your own allowed patterns:

```json
{
  "allow_patterns": [
    "rm -rf build/",
    "rm -rf dist/"
  ]
}
```

## Testing

Run the test suite:
```bash
python test_safety_hook.py
```

All 15 tests pass ✅

## Uninstall

Remove the hook entry from `~/.claude/settings.json`, or simply delete:
```bash
rm ~/.claude/hooks/safety_hook.py
```

## License

MIT License

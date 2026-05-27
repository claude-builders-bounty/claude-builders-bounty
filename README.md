# Pre-Tool-Use Safety Hook for Claude Code

A Python hook that blocks destructive bash commands before Claude Code executes them.

## Installation

### Step 1: Copy the hook script

```bash
mkdir -p ~/.claude/hooks && cp safety_hook.py ~/.claude/hooks/
```

### Step 2: Register the hook in settings

**If you already have `~/.claude/settings.json`**, merge the `hooks` section into your existing config:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "command": "python3 ~/.claude/hooks/safety_hook.py",
        "matcher": "Bash",
        "type": "command"
      }
    ]
  }
}
```

> **⚠️ Do NOT overwrite your existing `settings.json`!** Merge this with your current settings.
> If your file already has a `hooks` section, add the new entry to the `PreToolUse` array.

**If you don't have a settings.json yet:**

```bash
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

### Log Rotation

The log file is automatically rotated when it exceeds 1 MB (configurable via
the `SAFETY_HOOK_LOG_MAX_SIZE` environment variable). When rotated, the old
log is saved as `blocked.log.1`.

To disable rotation, set `SAFETY_HOOK_LOG_MAX_SIZE=0`.

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

The config file is cached in memory and automatically reloaded when the file changes.

## Testing

Run the test suite:

```bash
python test_safety_hook.py
```

Tests cover blocked commands, allowed commands, logging, and truncation behavior.

## Uninstall

Remove the hook entry from `~/.claude/settings.json`, or simply delete:

```bash
rm ~/.claude/hooks/safety_hook.py
```

## License

MIT License

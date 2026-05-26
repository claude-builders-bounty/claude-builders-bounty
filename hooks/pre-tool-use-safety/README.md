# Pre-tool-use safety hook

Blocks destructive Bash commands before Claude Code runs them.

## Install (2 steps)

1. Copy `hooks/pre-tool-use-safety/` into your project (or `~/.claude/hooks/`).
2. Register in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{ "command": "bash hooks/pre-tool-use-safety/hook.sh" }]
  }
}
```

## Test

```bash
bash hooks/pre-tool-use-safety/tests/test-hook.sh
```

Blocked attempts append to `~/.claude/hooks/blocked.log`.

# Issue #3 — Pre-tool-use Hook (Destructive Command Blocker)

Delivery for [claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## What was implemented

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

| File | Purpose |
|------|---------|
| `hooks/pre-tool-use-hook.sh` | Hook script — parses Claude Code JSON input, checks against blocklist |
| `hooks/README.md` | Installation instructions (2 commands) |

## Blocked patterns

| Pattern | Example |
|---------|---------|
| `rm -rf /`, `rm -rf *`, `rm -rf .` | Dangerous recursive removal |
| `DROP TABLE` | Database destruction |
| `git push --force` | Force push overwrite |
| `TRUNCATE TABLE` | Table truncation |
| `DELETE FROM table;` (no WHERE) | Unqualified deletion |

## Features

- **Logs every blocked attempt** to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
- **Clear error message** explaining why the command was blocked
- **Does not interfere** with normal bash commands (only blocks known-dangerous patterns)
- **Follows Claude Code hooks format** (reads JSON from stdin, exits 1 to block)

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use-hook.sh ~/.claude/hooks/
```

Then add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "preToolUse": "~/.claude/hooks/pre-tool-use-hook.sh"
  }
}
```

## Verification

```bash
echo '{"tool_input":{"command":"rm -rf /"}}' | bash hooks/pre-tool-use-hook.sh
# Exit code 1 — BLOCKED

echo '{"tool_input":{"command":"ls -la"}}' | bash hooks/pre-tool-use-hook.sh
# Exit code 0 — allowed
```

Closes #3

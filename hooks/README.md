# Destructive Command Blocker

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous
bash commands before they execute.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm --recursive` | Irreversible deletion |
| `DROP TABLE` | Destroys table + data permanently |
| `TRUNCATE [TABLE]` | Deletes all rows instantly |
| `DELETE FROM ...` (no WHERE) | Deletes ALL rows unintentionally |
| `git push --force` (not `--force-with-lease`) | Can overwrite remote history |

## Installation (2 commands)

```bash
# 1. Install the hook
mkdir -p ~/.claude/hooks && cp hooks/block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

# 2. Register with Claude Code
claude hooks add pre-tool-use bash ~/.claude/hooks/block-destructive.sh
```

Or manually add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "bash",
        "command": "~/.claude/hooks/block-destructive.sh"
      }
    ]
  }
}
```

## How It Works

1. Claude Code is about to run a `bash` command
2. The hook receives the command via stdin (JSON)
3. It checks the command against known destructive patterns
4. If dangerous: logs to `~/.claude/hooks/blocked.log`, returns block reason
5. If safe: allows the command to proceed

## What Is NOT Blocked

- `rm file.txt` (single file, no recursive)
- `git push` (without --force)
- `DELETE FROM users WHERE id = 5` (has WHERE clause)
- Normal shell commands: `ls`, `cat`, `grep`, `npm`, `node`, etc.

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-19T20:00:00Z] BLOCKED
  Command:  rm -rf /important/data
  Project:  /home/user/my-project
  Reason:   rm -rf is destructive and irreversible. Use trash or move to /tmp instead.
---
```

## Testing

```bash
# Test with a blocked command
echo '{"tool_input":{"command":"rm -rf /tmp/test"}}' | ~/.claude/hooks/block-destructive.sh
# Expected: {"continue":false,"reason":"rm -rf is destructive..."}

# Test with a safe command
echo '{"tool_input":{"command":"ls -la"}}' | ~/.claude/hooks/block-destructive.sh
# Expected: {"continue":true}
```

## Requirements

- `jq` (JSON processor)
- Claude Code (for hook registration)

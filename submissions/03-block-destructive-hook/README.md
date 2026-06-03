# 🔒 Block Destructive Commands — Claude Code Pre-Tool-Use Hook

A Claude Code hook that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Irreversible file deletion |
| `git push --force` | `git push origin main --force` | Destroys remote history |
| `DROP TABLE` | `DROP TABLE users;` | Destructive SQL |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Mass data deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Unfiltered row deletion |

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, working directory, and the full command.

## Setup (3 Steps)

```bash
# 1. Create the hooks directory
mkdir -p ~/.claude/hooks/pre-tool-use

# 2. Install the hook
cp block-destructive.sh ~/.claude/hooks/pre-tool-use/
chmod +x ~/.claude/hooks/pre-tool-use/block-destructive.sh

# 3. Restart Claude Code
# The hook is now active. Every bash command is checked before execution.
```

## How It Works

```
Claude wants to run: rm -rf node_modules/
                    │
                    ▼
        pre-tool-use hook (this script)
                    │
              ┌─────┴─────┐
              │  Pattern   │
              │  matching  │
              └─────┬─────┘
                    │
           ┌────────┴────────┐
           ▼                 ▼
     ✅ Allowed          🔴 Blocked
                    Logged to blocked.log
                    Claude told why
```

## Override

If you genuinely need to run a blocked command, temporarily disable the hook:

```bash
chmod -x ~/.claude/hooks/pre-tool-use/block-destructive.sh
# Run your command, then re-enable:
chmod +x ~/.claude/hooks/pre-tool-use/block-destructive.sh
```

## Testing

```bash
# Test blocked patterns
echo '{"command":"rm -rf /"}' | bash block-destructive.sh
# → {"is_approved": false, "msg": "..."}

echo '{"command":"git push origin main"}' | bash block-destructive.sh
# → {"is_approved": true}

# Check the log
cat ~/.claude/hooks/blocked.log
```

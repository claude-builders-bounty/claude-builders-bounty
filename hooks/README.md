# 🛡️ Block Destructive Bash Commands — Claude Code Hook

A **PreToolUse hook** for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks) that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive forced deletion — unrecoverable |
| `DROP TABLE` | Destroys database tables and data |
| `TRUNCATE` | Wipes all rows from a table |
| `git push --force` | Overwrites remote history (allows `--force-with-lease`) |
| `DELETE FROM` (no `WHERE`) | Deletes every row in a table |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Install (2 steps)

```bash
# 1. Copy hook and make executable
mkdir -p ~/.claude/hooks && \
curl -sL https://raw.githubusercontent.com/DrGalio/claude-builders-bounty/feature/block-destructive-hook/hooks/block-destructive.sh \
  -o ~/.claude/hooks/block-destructive.sh && \
chmod +x ~/.claude/hooks/block-destructive.sh

# 2. Register the hook in Claude Code
cat >> ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/block-destructive.sh"
      }]
    }]
  }
}
EOF
```

> **Note:** If you already have a `hooks` section in `~/.claude/settings.json`, merge the `PreToolUse` array instead of overwriting.

## How it works

```
Claude Code runs a Bash command
        │
        ▼
  PreToolUse fires
        │
        ▼
  block-destructive.sh reads command from stdin (JSON)
        │
        ▼
  ┌─ Dangerous? ─── YES ──→ Log to blocked.log
  │                          Return permissionDecision: "deny"
  │                          Claude sees the block, rethinks
  │
  └─ Safe? ────────────────→ exit 0 (command proceeds normally)
```

## Blocked log format

Each line in `~/.claude/hooks/blocked.log` is a JSON object:

```json
{"timestamp":"2026-03-27T03:30:00Z","command":"rm -rf node_modules","project":"/home/user/project","reason":"rm -rf: recursive forced deletion detected"}
```

## Disabling temporarily

To allow a specific dangerous command, temporarily rename the hook:

```bash
mv ~/.claude/hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh.disabled
# ... run your command ...
mv ~/.claude/hooks/block-destructive.sh.disabled ~/.claude/hooks/block-destructive.sh
```

## Testing

```bash
# Should be blocked
echo '{"tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/myproject"}' | ~/.claude/hooks/block-destructive.sh

# Should pass through
echo '{"tool_input":{"command":"ls -la"},"cwd":"/myproject"}' | ~/.claude/hooks/block-destructive.sh
```

## Requirements

- `bash` 4+
- `jq`
- Claude Code with hooks support

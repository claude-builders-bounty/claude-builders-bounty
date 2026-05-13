# ⛔ Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code safety hook that intercepts dangerous bash commands before execution, protecting your project from accidental destruction.

## 🚀 Install (2 commands)

```bash
# 1. Copy the hook to your Claude Code hooks directory
mkdir -p ~/.claude/hooks && cp hook.sh ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh

# 2. Add to your Claude Code settings (~/.claude/settings.json)
echo '{"hooks": {"pre_tool_use": [{"matcher": "Bash", "command": "bash ~/.claude/hooks/block-destructive.sh"}]}}' >> ~/.claude/settings.json
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /project` | Recursive force delete — permanently removes files |
| `DROP TABLE` | `DROP TABLE users` | Permanently deletes an entire database table |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Deletes all rows from a table |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Deletes ALL rows — missing WHERE clause |
| `git push --force` | `git push --force origin main` | Rewrites remote history, can lose others' work |

## How It Works

1. Claude Code calls this hook before every `Bash` tool invocation
2. The hook receives the command via stdin as JSON
3. It checks against a list of dangerous regex patterns
4. **Blocked** → returns `{ "decision": "block", "reason": "..." }` and logs the attempt
5. **Safe** → returns `{ "decision": "allow" }`

## Blocked Command Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-14 06:50:00] BLOCKED | project=/home/user/myapp | command="rm -rf node_modules" | reason=Recursive force delete (rm -rf) detected...
```

## Allowed Commands

These similar-but-safe commands pass through fine:

```bash
rm single_file.txt          # ✅ Not recursive force
rm -rf                      # ✅ No target path specified (harmless)
git push origin main        # ✅ Normal push
DELETE FROM users WHERE id=5  # ✅ Has WHERE clause
```

## Testing

```bash
# Test the hook manually
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /important"}}' | bash hook.sh
# Expected: {"decision": "block", ...}

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash hook.sh
# Expected: {"decision": "allow"}
```

## Files

- `hook.sh` — The hook script (bash + python3 for JSON parsing)
- `README.md` — This file
- `tests/` — Test cases

## Requirements

- Bash 4+
- Python 3.6+ (for JSON parsing)
- Claude Code with hooks support

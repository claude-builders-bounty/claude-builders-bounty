# block-destructive.sh — Claude Code Safety Hook

Pre-tool-use hook that intercepts dangerous bash commands before execution.

## Setup (3 steps)

```bash
# 1. Install the hook script
mkdir -p ~/.claude/hooks
cp block-destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh

# 2. Add to your Claude Code settings
# Merge settings-snippet.json into ~/.claude/settings.json

# 3. Start using Claude Code — protection is automatic
```

## What It Blocks

| Category | Patterns | Example |
|----------|----------|---------|
| **Filesystem** | `rm -rf /`, `rm -rf /*`, `dd to /dev/sd*`, `mkfs.*` | `rm -rf /etc` ❌ |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` | `DELETE FROM users` ❌ |
| **Git Force** | `git push -f`, `git push --force`, `git reset --hard`, `git clean -f` | `git push --force origin main` ❌ |
| **Fork Bomb** | `:() { :|:& };:` | Shell fork bombs ❌ |
| **System** | `shutdown -h now`, `reboot`, `chmod -R 777 /` | `shutdown now` ❌ |

All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Safe Commands (still allowed)

- `rm file.txt` ✅ — single files are fine
- `rm -rf node_modules` ✅ — project-level cleanup
- `git push origin main` ✅ — no force flag
- `DELETE FROM users WHERE id=5` ✅ — has WHERE clause
- `DROP TABLE IF EXISTS temp_data` ✅ — explicit IF EXISTS

## Dry Run Mode

To only warn instead of blocking, edit the script and set `DRY_RUN=true`.

## How It Works

```
Claude generates Bash command
        ↓
PreToolUse hook fires (block-destructive.sh)
        ↓
Script checks command against 21+ dangerous patterns
        ↓
  ┌─ Safe ──────────→ {"continue": true} → Command runs
  │
  └─ Dangerous ─────→ {"continue": false} → Blocked + logged
```

## Bounty

[claude-builders-bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100

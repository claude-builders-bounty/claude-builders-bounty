# 🛡️ Block Dangerous Commands — Claude Code Pre-Tool-Use Hook

**Bounty:** [#3 — HOOK: Pre-tool-use hook that blocks destructive bash commands](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)
**Reward:** $100
**Status:** ✅ Submitted

## Overview

A pre-tool-use hook for Claude Code that intercepts and blocks dangerous shell commands before they execute. Prevents accidental data loss from destructive operations.

## Quick Install (≤ 2 commands)

### 1. Install Hook

```bash
# Create hooks directory and install
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/block-dangerous-commands.sh \
  https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/submissions/3-pre-tool-use-hook/block-dangerous-commands.sh
chmod +x ~/.claude/hooks/block-dangerous-commands.sh
```

### 2. Configure in `.claude/settings.json`

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "command": ["bash", "~/.claude/hooks/block-dangerous-commands.sh"],
        "timeout": 5000
      }
    ]
  }
}
```

## Blocked Operations

| Pattern | Severity | Reason |
|---------|----------|--------|
| `rm -rf /` | 🔴 CRITICAL | Recursive root deletion |
| `DROP TABLE` | 🔴 CRITICAL | Destructive DB operation |
| `TRUNCATE TABLE` | 🟠 HIGH | Table data loss |
| `DELETE FROM` (no WHERE) | 🟠 HIGH | Unconditional delete |
| `UPDATE ... SET` (no WHERE) | 🟠 HIGH | Unconditional update |
| `git push --force` | 🔴 CRITICAL | Force push — history rewrite |
| `git reset --hard` | 🟠 HIGH | Discard uncommitted changes |
| `chmod 777` | 🟠 HIGH | Overly permissive |
| `git branch -D` | 🟠 HIGH | Force delete branch |
| `mkfs.`, `fdisk`, `dd if=` | 🔴 CRITICAL | Filesystem/Disk operations |
| `DROP DATABASE` | 🔴 CRITICAL | Database destruction |

## Allowlist

To allow specific patterns, create `~/.claude/hooks/.dangerous-allowlist`:

```bash
# One regex pattern per line
TRUNCATE TABLE temp_logs
git push --force my-feature-branch
```

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:
```
[2026-07-10T22:30:00Z] [CRITICAL] [hostname] [user] Blocked: rm -rf /var/log — Recursive force delete
[2026-07-10T22:31:00Z] [HIGH] [hostname] [user] Blocked: git push --force — Force push
```

## Testing

- ✅ Blocks `rm -rf /`
- ✅ Blocks `DROP TABLE users`
- ✅ Blocks `git push --force origin main`
- ✅ Blocks `DELETE FROM logs` (no WHERE)
- ✅ Allows safe commands (`git push`, `rm file.txt`, `SELECT`)
- ✅ Logs all blocks to `blocked.log`
- ✅ Allowlist overrides blocking

## Files

- `block-dangerous-commands.sh` — Hook script
- `README.md` — This file

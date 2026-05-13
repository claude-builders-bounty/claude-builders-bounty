# Bash Guard Hook — pre-tool-use safety filter
> **Bounty $100**
## Overview

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before
execution. Written in Python, zero dependencies.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Claude Code automatically discovers and runs hooks from `~/.claude/hooks/`.

## Blocked Patterns

| Category | Patterns Blocked |
|----------|-----------------|
| Destructive rm | `rm -rf /`, `rm -rf *`, `rm -rf .` |
| Database drops | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` |
| Dangerous DELETE | `DELETE FROM` without WHERE clause |
| Force push | `git push --force`, `git push --delete` |
| Block device writes | `dd` to `/dev/`, `> /dev/sda` |
| Fork bombs | `:(){ :\|:& };:` pattern |
| Permission chaos | `chmod 777`, `chown` on root/home |
| System file overwrites | `> /etc/passwd`, `> /etc/shadow` |
| Pipe-to-shell | `curl ... \| sh`, `wget ... \| bash` |

## Smart Allowlist

Common safe operations are auto-allowlisted:
- `rm -rf node_modules`
- `rm -rf dist`
- `rm -rf .next`
- `rm -rf .turbo`
- `rm -rf coverage`
- `rm -rf /tmp/<specific>`

## 🛡️ Logging & Audit

All blocked attempts are logged for security auditing:

- **Path**: `~/.claude/hooks/blocked.log`
- **Format**: `[YYYY-MM-DD HH:MM:SS] BLOCKED | CWD: <path> | Command: <cmd> | Reason: <reason>`

**Audit Log Sample** (captured from real execution on 2026-05-13):
```
[2026-05-13 03:47:28] BLOCKED | CWD: /home/user/production | Command: rm -rf / | Reason: rm targeting root or home directory
[2026-05-13 03:47:28] BLOCKED | CWD: /var/lib/postgresql | Command: DROP TABLE users | Reason: DROP TABLE/DATABASE
[2026-05-13 03:47:28] BLOCKED | CWD: /home/user/repo | Command: git push --force origin main | Reason: git push --force
```

> _Each entry records timestamp, working directory, full command, and the specific blocking reason — no generic "high-risk" labels._

**How to view the log:**
```bash
cat ~/.claude/hooks/blocked.log        # Show all blocked attempts
tail -f ~/.claude/hooks/blocked.log    # Watch live as blocks happen
wc -l ~/.claude/hooks/blocked.log      # Count total blocked commands
```

## Testing

```bash
# Should BLOCK:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | python3 pre-tool-use
echo $?  # → 1

# Should ALLOW:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf node_modules"}}' | python3 pre-tool-use
echo $?  # → 0

# Verify log was written:
cat ~/.claude/hooks/blocked.log
```

## Compliance

- Claude Code hooks format v2 (JSON stdin → JSON stdout + exit code)
- No external dependencies (stdlib only)
- Extensible: add patterns to `BLOCK_PATTERNS`, `ALLOWLIST`

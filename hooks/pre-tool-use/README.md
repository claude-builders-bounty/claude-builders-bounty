# Pre-Tool-Use Safety Hook 🛡️

A Claude Code `pre-tool-use` hook that intercepts destructive bash commands before execution.

## What It Blocks

| Category | Patterns |
|----------|----------|
| **File deletion** | `rm -rf /`, `rm -rf ~`, `rm -rf *`, `rm -rf .`, system dirs (`/etc`, `/home`, `/usr`, `/var`, `/boot`, etc.) |
| **SQL destruction** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` (no `WHERE`) |
| **Git danger** | `git push --force`, `git reset --hard HEAD~` |
| **Disk operations** | `dd of=/dev/sd*`, `mkfs.*`, `fdisk`, `shred` |
| **Firewall** | `iptables -F`, `ufw disable` |
| **System** | Fork bombs, `chmod 777 /`, `chown -R /`, `kill -9 1` |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hook.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

Claude Code sends hook input as JSON via stdin:
```json
{"tool": "bash", "args": {"command": "rm -rf /"}}
```

The hook checks the command and responds:
```json
{"allow": false, "reason": "⛔ BLOCKED: Recursive force delete from root..."}
```

Safe commands pass through: `{"allow": true}`

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:
```
[2026-04-14 12:00:00 UTC] ⛔ BLOCKED: Recursive force delete from root | cmd: rm -rf / | cwd: /home/user/project
```

## Test

```bash
# Run the test suite
python3 test_hook.py

# Quick manual test
echo '{"tool":"bash","args":{"command":"rm -rf /"}}' | python3 hook.py
# → {"allow": false, "reason": "⛔ BLOCKED: Recursive force delete from root..."}
```

## Design Decisions

- **Python 3** — no external dependencies, robust regex, reliable JSON parsing
- **Fail-open** — if the hook crashes or can't parse input, it allows the command (safe defaults)
- **Case-insensitive** — catches `DROP TABLE` and `drop table`
- **Precise matching** — allows `rm -rf /tmp/workdir` but blocks `rm -rf /`
- **Non-destructive only** — doesn't interfere with normal bash commands

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

---

Closes #3

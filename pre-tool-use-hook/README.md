# 🛡️ Pre-Tool-Use Hook: Destructive Command Blocker

**Bounty: $100** — A Claude Code pre-tool-use hook that blocks destructive bash commands.

## Installation

```bash
git clone https://github.com/mkcash/claude-builders-bounty.git
ln -sf "$(pwd)/pre-tool-use-hook/hooks/pre_tool_use.py" ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example | Reason |
|---------|---------|--------|
| `rm -rf /` | `rm -rf /var/log` | Destructive recursive deletion |
| `rm -rf *` | `rm -rf ./*` | Wildcard deletion |
| `git push --force` | `git push --force main` | Overwrites remote history |
| `DROP TABLE/DB` | `DROP TABLE users` | Destructive database operation |
| `TRUNCATE` | `TRUNCATE orders` | Table truncation |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Unqualified deletion |
| `mkfs/fdisk/dd` | `dd if=/dev/zero of=/dev/sda` | Filesystem destruction |
| `chmod -R 777` | `chmod -R 777 /etc` | Overly permissive permissions |
| `shutdown/reboot` | `shutdown -h now` | System shutdown |

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path

## How It Works

The hook intercepts bash commands via Claude Code's pre-tool-use hook mechanism.
It parses the incoming tool use JSON, extracts the command, and checks it against
a set of dangerous patterns. If matched, it blocks execution and logs the attempt.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

---

**License:** MIT

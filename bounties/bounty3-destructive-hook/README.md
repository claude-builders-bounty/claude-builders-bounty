# 🛡️ Destructive Command Guard

> **Bounty #3** — Pre-tool-use hook that blocks destructive bash commands in Claude Code.

## Installation

Two commands:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete — no undo |
| `DROP TABLE/DATABASE` | Destructive DDL — can't be rolled back |
| `TRUNCATE` | Table truncation — all data lost |
| `DELETE FROM` (no WHERE) | Unconditional delete |
| `git push --force` / `-f` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted changes |
| `git clean -fd` | Permanently removes untracked files |
| `mkfs.*` | Filesystem creation — destroys existing data |
| `dd if=... of=...` | Raw disk write |
| `shutdown` / `reboot` / `poweroff` | System operations |
| `chmod 777` | Overly permissive permissions |
| `sudo apt remove/purge` | Package removal |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:

- Timestamp
- Blocked command
- Reason
- Project path

## Testing

```bash
# These should be blocked:
echo '{"command": "rm -rf /tmp/test"}' | python3 pre-tool-use
echo '{"command": "DROP TABLE users"}' | python3 pre-tool-use
echo '{"command": "git push --force origin main"}' | python3 pre-tool-use

# These should be allowed:
echo '{"command": "ls -la"}' | python3 pre-tool-use
echo '{"command": "npm install"}' | python3 pre-tool-use
echo '{"command": "git push origin main"}' | python3 pre-tool-use

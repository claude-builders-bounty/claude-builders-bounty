# Pre-Tool-Use Safety Hook

Blocks destructive bash commands before they execute in Claude Code / Hermes.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -sL https://raw.githubusercontent.com/3275113459/claude-builders-bounty/main/skills/safety-hook/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `git push --force` | Force push (rewrites history) |
| `git reset --hard` | Discards uncommitted changes |
| `DROP TABLE` / `DROP DATABASE` | Destructive database operations |
| `TRUNCATE` | Table truncation |
| `DELETE FROM` (no WHERE) | Mass deletion |
| `mkfs` / `dd if= of=` | Filesystem/disk formatting |
| `chmod -R 777` | World-writable permissions |
| `apt remove/purge` | Package removal |
| `rm *.key/wallet/keystore` | Delete sensitive files |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:
```
[2026-06-04 22:30:00] BLOCKED: Recursive force delete
  Command: rm -rf /data
  Project: /home/user/myproject
```

## Wallet

0x53b0957b9d7c86c6c20463e945044cd722227728

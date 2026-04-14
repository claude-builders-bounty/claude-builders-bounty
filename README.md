# Claude Code Destructive Command Blocker

A pre-tool-use hook that intercepts and blocks dangerous bash commands before Claude Code executes them.

## Install (2 commands)

```bash
cp -r hooks ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh
```

## What It Blocks

| Pattern | Risk |
|---|---|
| `rm -rf /`, `rm -rf ~`, `rm -rf *` | Mass file deletion |
| `DROP TABLE`, `TRUNCATE` | Database destruction |
| `DELETE FROM` (without WHERE) | Unbounded data deletion |
| `git push --force` | Git history rewrite |
| `mkfs`, `dd if=` | Disk destruction |
| `chmod -R 777 /` | Permission escalation |
| Fork bombs | Resource exhaustion |

## Smart Safeguards

The hook allows commands that include safety mechanisms:
- `rm -rf --preserve-root` — protected root deletion
- `DROP TABLE IF EXISTS` — safe table drops
- `DELETE FROM ... WHERE ...` — bounded deletes
- `git push --force-with-lease` — safer force push

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601 UTC)
- Matched pattern
- Full command
- Project path

### Example log entry

```
[2026-04-14T01:30:00Z] BLOCKED | Pattern: rm -rf / | Command: rm -rf /tmp/old-project | Project: /home/user/myapp
```

## How It Works

1. Claude Code passes bash command input via stdin (JSON format)
2. The hook parses the command and checks against dangerous patterns
3. If matched (without safety override), it logs the attempt and returns `block`
4. Claude receives the block decision and explains to the user

## Claude Code Hooks

This follows the Claude Code hooks format in `~/.claude/hooks/`. See [Claude Code hooks docs](https://docs.anthropic.com/claude-code/hooks) for more information.

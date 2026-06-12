# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code hook that intercepts dangerous bash commands before they execute.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
curl -sL https://raw.githubusercontent.com/laogongcy-del/claude-builders-bounty/main/submissions/pre-tool-use-hook/block-destructive.py -o ~/.claude/hooks/pre-tool-use/block-destructive && chmod +x ~/.claude/hooks/pre-tool-use/block-destructive
```

## What it blocks

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -fr` | `rm -rf /data` | File destruction |
| `DROP TABLE/DATABASE/SCHEMA` | `DROP TABLE users` | Data loss |
| `DELETE FROM` without WHERE | `DELETE FROM users` | Mass deletion |
| `TRUNCATE` | `TRUNCATE orders` | Data loss |
| `git push --force` | `git push --force origin main` | Remote overwrite |
| `chmod -R 000` | `chmod -R 000 /var` | Permission lockout |
| `curl ... \| bash` | `curl http://x.sh \| bash` | Remote code execution |

## Logs

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-12T10:30:00] BLOCKED | reason=Recursive force delete | cmd=rm -rf /data/tmp
```

## Requirements

- Python 3.6+
- Claude Code

## How it works

The hook receives tool call data as JSON on stdin. When a `Bash` tool call contains a dangerous pattern, it exits with code 1 (blocked) and displays a clear message. Safe commands pass through with exit code 0.

# Claude Safe Hook

Pre-tool-use hook that blocks destructive bash commands before execution.

## Installation (2 commands)

```bash
# 1. Copy the hook to ~/.claude/hooks/
mkdir -p ~/.claude/hooks
cp hook.sh ~/.claude/hooks/pre-tool-use

# 2. Enable in Claude Code settings.json
# Add to your Claude Code settings:
# {
#   "hooks": {
#     "pre-tool-use": "~/.claude/hooks/pre-tool-use"
#   }
# }
```

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf /` | System destruction |
| `DROP TABLE` | Database destruction |
| `TRUNCATE TABLE` | Database destruction |
| `DELETE FROM` without WHERE | Data loss |
| `git push --force` | History rewrite |
| `ALTER TABLE DROP` | Schema destruction |
| `sudo rm` | Escalated deletion |
| `mkfs` | Filesystem destruction |
| Fork bomb | DoS |
| `dd` to /dev | Device destruction |
| Pipe to shell | Arbitrary code execution |

## Log Location

All blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Format:
```
[2026-03-30 13:27:00] BLOCKED: rm -rf / | Reason: rm\s+-rf\s+/ | Project: /path/to/project
```

## For Claude Code

Add to your settings:
```json
{
  "hooks": {
    "pre-tool-use": "bash ~/.claude/hooks/pre-tool-use"
  }
}
```

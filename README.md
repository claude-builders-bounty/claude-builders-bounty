# Bash Guard — Claude Code Pre-Tool-Use Hook

Blocks dangerous bash commands before Claude Code executes them.

## Quick Start

```bash
# 1. Install
mkdir -p ~/.claude/hooks && cp scripts/bash-guard-hook.py ~/.claude/hooks/bash-guard
chmod +x ~/.claude/hooks/bash-guard

# 2. Configure Claude Code to use it
echo '{"hooks": {"pre-tool-use": [{"tool": "bash", "command": "~/.claude/hooks/bash-guard"}]}}' >> ~/.claude/config.json
```

## Blocked Commands

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Irreversible database operation |
| `TRUNCATE TABLE` | Removes all rows |
| `DELETE FROM` without `WHERE` | Deletes all rows |
| `git push --force` / `-f` | Overwrites remote history |
| `chmod 777` | World-writable permissions |
| `sudo rm -rf /` | System destruction |
| Fork bombs, block device writes | Malicious patterns |

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:
```json
{"timestamp": "2026-05-14T12:00:00Z", "command": "rm -rf /tmp/*", "cwd": "/home/user/project", "reason": "BLOCKED: rm -rf (recursive force delete)"}
```

## Override

In an emergency, set the environment variable:
```bash
export CLAUDE_ALLOW_DANGEROUS=1
```

## Does NOT Interfere With

- Normal `rm` (single file)
- `rm -r` without `-f`
- `DELETE FROM ... WHERE id = 5`
- Regular `git push`
- Any non-bash tool calls

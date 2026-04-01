# Claude Code Pre-Tool-Use Hook

Blocks destructive bash commands before execution.

## Setup

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "preToolUse": {
      "bash": "/path/to/hook.sh"
    }
  }
}
```

## Blocked Patterns

- `rm -rf`, `rm -r /`, recursive home deletion
- Disk operations (`dd`, `mkfs`, `/dev/sda`)
- System commands (`shutdown`, `reboot`, `halt`)
- Insecure permissions (`chmod 777`)
- Force git operations (`push --force`, `reset --hard`)
- SQL destruction (`DROP TABLE`, `TRUNCATE`)
- Pipe-to-shell (`curl|sh`, `wget|sh`)

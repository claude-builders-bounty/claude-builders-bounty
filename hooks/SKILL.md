---
name: block-destructive-commands
description: Pre-tool-use hook that blocks destructive bash commands in Claude Code
version: 1.0.0
author: fenn Alexander
trigger: PreToolUse
matcher: Bash
---

# Block Destructive Commands

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before they execute.

## Installation

1. Copy `hooks/pre_tool_use_block_destructive.py` and `hooks/blocklist.json` to your project
2. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "CLAUDE_HOOK_NAME=PreToolUse python3 \"/path/to/pre_tool_use_block_destructive.py\""
        }]
      }
    ]
  }
}
```

## Blocked Patterns

- `rm -rf /` — Recursive root delete
- `DROP DATABASE/TABLE` — SQL data destruction
- `TRUNCATE` — Table truncation (except temp/test tables)
- `mkfs` / `dd of=/dev/` — Disk formatting
- `sudo rm` — Privileged delete
- `curl | sh` — Remote script execution
- `chmod 777 /` — Insecure permissions
- `git push --force main` — Force push to main
- `npm publish` — Unintended package publish
- `docker system prune` — Container cleanup

## Customization

Edit `blocklist.json` to add/remove patterns. Allowed patterns take precedence over blocked patterns.

## Logging

Blocked commands are logged to `~/.claude/hooks/blocked.log`.

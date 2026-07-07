# Pre-Tool-Use Hook - Destructive Command Blocker

Installs a Claude Code hook that intercepts dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks/
cp pre-tool-use-hook.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Add to `~/.claude/claude.md`:
```
Hook pre-tool-use: python3 ~/.claude/hooks/pre_tool_use.py
```

## Blocked Patterns
- `rm -rf /`, `~`, `/etc`, `/var`, `/usr`
- `git push --force`
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- `DELETE FROM` / `UPDATE` without WHERE clause
- `chmod -R 777`, `chown -R`
- `mkfs`, `dd` destructive operations
- System commands: shutdown, reboot, init

## Logging
All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

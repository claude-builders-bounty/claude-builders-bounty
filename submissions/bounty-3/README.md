# Pre-Tool-Use Hook: Destructive Bash Command Blocker
### Bounty #3 - $100

A Claude Code pre-tool-use hook that intercepts dangerous bash commands.

## Blocked Commands (25+ patterns)
- rm -rf / recursive force deletes
- dd to raw devices, filesystem formats
- DROP TABLE/DATABASE/SCHEMA, TRUNCATE
- DELETE FROM without WHERE
- git push --force, git reset --hard
- shutdown, reboot, halt, poweroff
- iptables flush, fork bombs
- and more...

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks
cp submissions/bounty-3/pre-tool-use-hook.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-hook.py
```

## CLAUDE.md Config
```yaml
hooks:
  PreToolUse:
    - command: "python3 ~/.claude/hooks/pre-tool-use-hook.py"
```

## Log Format (~/.claude/hooks/blocked.log)
```json
{"timestamp":"2026-08-11T10:30:00Z","command":"rm -rf /etc","reason":"rm -rf","project_path":"/home/user","action":"BLOCKED"}
```

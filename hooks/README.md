# Destructive Command Blocker — Claude Code PreToolUse Hook

> **Bounty #3 ($100)** — Block destructive bash/PowerShell commands before execution

A `pre_tool_use` hook that intercepts dangerous commands before they execute.
Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`,
`DELETE FROM` without WHERE, `curl|bash` pipes, and 20+ more patterns.

## Quick Install (2 commands)

```bash
# 1. Copy hook
cp hooks/pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py

# 2. Add to ~/.claude/settings.json:
# "hooks": {"pre_tool_use": [{"matcher": "Bash|PowerShell",
#   "hooks": [{"type": "command",
#   "command": "python3 ~/.claude/hooks/pre_tool_use.py"}]}]}
```

## What It Blocks

| Category | Patterns | Risk |
|---|---|---|
| Filesystem | `rm -rf`, `dd if=`, `mkfs`, `chmod 777` | Data loss |
| Git | `push --force`, `reset --hard`, `clean -fdx` | History loss |
| Database | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (no WHERE) | Data loss |
| Injection | `curl\|bash`, `wget\|sh`, `eval` | RCE |
| Infra | `docker system prune`, `kubectl delete ns`, `aws s3 rm` | Infra damage |

## Logging

Blocked attempts logged to `~/.claude/hooks/blocked.log` as JSON with
timestamp, command, matched patterns, and project path.

## Testing

```bash
# Should BLOCK
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /x"}}' | python3 pre_tool_use.py

# Should ALLOW
echo '{"tool_name":"Bash","tool_input":{"command":"echo hello"}}' | python3 pre_tool_use.py
```

All 4 acceptance criteria tests pass (rm -rf blocked, DROP TABLE blocked,
git push --force blocked, safe commands allowed through).

# Empire Shield Hook — Block Destructive Bash Commands

**Bounty:** #3 — $100 (Opire)

A Claude Code **pre-tool-use** hook that intercepts and blocks destructive bash commands before execution.

## Installation

### 1-Click Install
```bash
mkdir -p ~/.claude/hooks && curl -L https://raw.githubusercontent.com/jiezishu000/claude-builders-bounty/solution/hook-block-destructive/hooks/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

### Configure
Add to your `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/pre-tool-use" }] }
    ]
  }
}
```

Done. Only 2 steps.

## Blocked Patterns

| Command | Example |
|---|---|
| `rm -rf` | `rm -rf /project` |
| `rm -r` | `rm -r src/` |
| `DROP TABLE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE orders` |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` |
| `git push --force` | `git push origin main --force` |
| `git reset --hard` | `git reset --hard HEAD~3` |

## Logging
All blocked commands logged to `~/.claude/hooks/blocked.log`:
```
2026-05-14T12:30:00Z | BLOCKED | Bash | rm -rf /important | /home/user/project
```

## Testing
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /test"}}' | bash hooks/pre-tool-use
# => {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"SECURITY: ..."}}
```

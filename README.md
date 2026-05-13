# ⚠️ Pre-Tool-Use Hook: Destructive Command Guard

A [Claude Code](https://docs.anthropic.com/claude-code) `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## Installation

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/extremeWu/claude-builders-bounty/main/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

**That's it.** Claude loads the hook automatically on the next `/thinking` or tool use.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete (irreversible) |
| `DROP TABLE` | Destructive SQL operation |
| `git push --force` / `git push -f` | Force push rewrites remote history |
| `TRUNCATE` | Destructive SQL operation |
| `DELETE FROM` (without `WHERE`) | Mass deletion of all rows |

## What It Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log` in JSON format:

```json
{"timestamp": "2026-05-13T16:45:00", "command": "rm -rf /project/data", "reason": "rm -rf: Recursive force delete", "project": "/home/user/my-project"}
```

## How It Works

1. Claude calls the hook with a JSON payload on stdin before executing each `bash` tool use
2. The hook checks the command against the dangerous patterns list
3. If matched → blocks execution, logs the attempt, returns a clear explanation
4. If safe → allows execution immediately

The hook **fails open** — if anything goes wrong (JSON parse error, etc.), the command is allowed.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## Development

To test locally:

```bash
# Test a blocked command
echo '{"tool_use":{"name":"bash","input":{"command":"rm -rf /tmp/test"}}}' | python3 pre-tool-use

# Test an allowed command
echo '{"tool_use":{"name":"bash","input":{"command":"ls -la"}}}' | python3 pre-tool-use
```

## License

MIT

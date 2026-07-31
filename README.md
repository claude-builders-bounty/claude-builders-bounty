# Claude Code: Pre-Tool-Use Hook — Block Destructive Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands
before execution, logs blocked attempts, and explains why each command
was blocked.

## Blocked Patterns

| Pattern | Example | Reason |
|---------|---------|--------|
| `rm -rf` | `rm -rf /tmp/build` | Recursive force remove |
| `DROP TABLE` | `DROP TABLE users` | Destructive database operation |
| `TRUNCATE` | `TRUNCATE users` | Destructive database operation |
| `DELETE FROM` (no WHERE) | `DELETE FROM orders` | Would delete all rows |
| `git push --force` | `git push -f origin main` | Destructive remote push |

## Installation

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
ln -s "$PWD/hooks/pre-tool-use/block-destructive.sh" ~/.claude/hooks/pre-tool-use/
```

That's it. Claude Code will pick up the hook on the next session.

## How It Works

1. Claude Code sends tool-call JSON via stdin before executing Bash commands
2. The hook checks the `command` field against blocked patterns
3. If a match is found: the hook logs the attempt to `~/.claude/hooks/blocked.log`, returns a denial, and tells Claude why
4. If safe: the hook passes the command through unchanged

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-07-31T17:00:00Z] BLOCKED: rm -rf (recursive force remove)
  Command: rm -rf /important/dir
  Project: /Users/me/project
```

## Testing

```bash
# Should be blocked (exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/test"}' \
  | bash hooks/pre-tool-use/block-destructive.sh

# Should be allowed (exit 0)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/test"}' \
  | bash hooks/pre-tool-use/block-destructive.sh
```

## License

MIT

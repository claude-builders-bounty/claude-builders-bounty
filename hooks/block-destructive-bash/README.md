# HOOK: Block Destructive Bash Commands

A Claude Code **PreToolUse** hook that intercepts and blocks dangerous bash commands before they execute.

## Blocked Patterns

| Pattern | Example |
|---|---|
| `rm -rf` | `rm -rf /`, `rm -fr /tmp`, `rm -r -f dir` |
| `DROP TABLE` | `mysql -e 'DROP TABLE users'` |
| `git push --force` / `-f` | `git push --force origin main` |
| `TRUNCATE` | `psql -c 'TRUNCATE TABLE users'` |
| `DELETE FROM` without `WHERE` | `mysql -e 'DELETE FROM users'` |

All SQL patterns are matched case-insensitively. Normal commands (`rm file.txt`, `git push`, `DELETE FROM ... WHERE ...`) pass through unaffected.

## Install (2 commands)

```bash
cp block-destructive.sh ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh
claude settings set hooks.PreToolUse '[{"matcher":"Bash","hooks":[{"type":"command","command":"bash \"$HOME/.claude/hooks/block-destructive.sh\""}]}]'
```

## How It Works

1. Claude Code fires a `PreToolUse` event before every Bash tool call
2. The hook reads the JSON input from stdin, extracts the command
3. Checks the command against destructive patterns
4. If matched: logs to `~/.claude/hooks/blocked.log` and returns `permissionDecision: "deny"`
5. If safe: exits 0 (allow)

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2025-01-15T10:30:00Z | BLOCKED | BLOCKED: 'rm -rf' detected. Recursive force deletion is not allowed. | project=/home/user/myproject | command=rm -rf /tmp/build
```

## Requirements

- `bash`, `jq` (standard on most systems)

## Tests

```bash
bash test-block-destructive.sh
```

## Files

| File | Purpose |
|---|---|
| `block-destructive.sh` | The hook script |
| `settings.json` | Example Claude Code settings snippet |
| `test-block-destructive.sh` | Automated tests |
| `README.md` | This file |

## License

MIT

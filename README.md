# Claude Code — Destructive Command Guard Hook

A `pre-tool-use` hook that intercepts dangerous bash commands **before** execution.

## Quick Install

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. The hook runs automatically on every Claude Code tool invocation.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Destructive recursive delete |
| `git push --force` / `git push -f` | Overwrites remote history |
| `DROP TABLE` | Deletes entire database tables |
| `TRUNCATE` | Empties database tables |
| `DELETE FROM` (no WHERE) | Deletes all rows |

## How It Works

1. Claude Code passes tool-call info as JSON on stdin
2. The hook checks the command against a pattern list
3. **Safe commands** → exit 0 (let through)
4. **Dangerous commands** → exit 1 (block), logs the attempt

## Logging

Blocked attempts are logged to:

```
~/.claude/hooks/blocked.log
```

Format: `[timestamp] reason | command | project path`

## Customization

Edit `DANGEROUS_PATTERNS` in the script to add or remove patterns.

## Files

- `pre-tool-use` — the hook script (Python 3)
- `README.md` — this file

## License

Licensed under the MIT License — see [LICENSE](LICENSE).

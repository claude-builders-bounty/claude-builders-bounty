# pre-tool-use Hook — Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf /` | `rm -rf /var/log` | Recursive system delete |
| `DROP TABLE` | `DROP TABLE users;` | Destructive database operation |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs;` | Destructive table truncation |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Unconditionally deletes all rows |

## What It Allows

- `rm file` — single file delete (safe)
- `rm -rf ./node_modules` — local directory delete (safe)
- `git push` — normal push (safe)
- `git push --force-with-lease` — safer force push (allowed)
- `DELETE FROM users WHERE id = 5` — conditional delete (safe)
- All other normal bash commands

## Logging

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:
```
[2026-06-26T12:00:00Z] BLOCKED | project=/home/user/project | cmd=rm -rf /var | reason=Recursive delete of system directory
```

## Disable Temporarily

```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled
```

Re-enable: `mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use`

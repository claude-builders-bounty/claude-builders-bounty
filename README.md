# Bounty #3 — Pre-tool-use Hook: Block Destructive Commands

A Claude Code pre-tool-use hook that intercepts dangerous bash commands before execution.

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /`, `rm -rf ./node_modules` |
| `DROP TABLE` | `DROP TABLE users;` (case-insensitive) |
| `git push --force` | `git push --force`, `git push -f`, `git push --force-with-lease` |
| `TRUNCATE` | `TRUNCATE users;` (case-insensitive) |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` but allows `DELETE FROM users WHERE id = 1;` |

## Installation (2 commands)

```bash
git clone https://github.com/fitzerooqq/claude-builders-bounty.git /tmp/bounty3
bash /tmp/bounty3/install.sh
```

Then add the hook config from the installer output to `~/.claude/settings.json` or `.claude/settings.json`.

## How It Works

1. Claude Code invokes the hook before every `Bash` tool call
2. The hook reads the tool input JSON from stdin
3. It checks the command against dangerous patterns
4. If dangerous: prints a red warning to stderr, logs to `~/.claude/hooks/blocked.log`, and outputs a JSON deny decision to stdout
5. If safe: exits 0 (allows execution)

## Blocked Log

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Reason for blocking
- Full command text
- Project directory path

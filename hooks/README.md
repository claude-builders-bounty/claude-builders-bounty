# Safe Claude: Block Destructive Commands

A pre-tool-use hook for Claude Code that intercepts and blocks dangerous bash commands before they execute.

## Blocked Patterns

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete — destroys files permanently |
| `DROP TABLE` | Deletes database table and all data |
| `git push --force` | Overwrites remote history |
| `TRUNCATE TABLE` | Instantly removes all rows |
| `DELETE FROM` (no WHERE) | Deletes ALL rows from table |

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -sL https://raw.githubusercontent.com/laogongcy-del/claude-builders-bounty/feat/block-destructive-commands-hook/hooks/block-destructive-commands.sh -o ~/.claude/hooks/block-destructive-commands.sh && chmod +x ~/.claude/hooks/block-destructive-commands.sh
```

## How It Works

1. Claude Code calls the hook before executing any bash command
2. The hook checks the command against dangerous patterns
3. If blocked: logs to `~/.claude/hooks/blocked.log` and tells Claude why
4. If safe: silently allows the command

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-12T10:30:00Z] BLOCKED: rm -rf | Command: rm -rf /tmp/project | Project: /home/user/myproject
```

## Uninstall

```bash
rm ~/.claude/hooks/block-destructive-commands.sh
```

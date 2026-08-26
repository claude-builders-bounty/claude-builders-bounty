# block-destructive

A [Claude Code](https://claude.ai/code) `PreToolUse` hook that blocks dangerous bash commands before they execute.

## Blocked Patterns

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` | Irreversible recursive deletion |
| `DROP TABLE` | Destroys database schema |
| `TRUNCATE TABLE` | Destroys all table data |
| `git push --force` / `git push -f` | Rewrites remote history |
| `DELETE FROM` | Mass row deletion without WHERE clause |

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, project path, and the attempted command.

## Install (2 commands)

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks && cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

# 2. Add to ~/.claude/settings.json (merge with existing config)
jq '.hooks.PreToolUse += [{"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/block-destructive.sh"}]}]' ~/.claude/settings.json > /tmp/settings.tmp && mv /tmp/settings.tmp ~/.claude/settings.json
```

If you don't have `jq`, add this manually to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Claude Code fires `PreToolUse` before every Bash command
2. The hook reads the command from stdin (JSON)
3. If the command matches a dangerous pattern, it returns `permissionDecision: "deny"`
4. Claude receives the reason and can adjust its approach
5. Normal commands pass through unmodified

## Log Format

```
2026-08-26T23:00:00Z | /path/to/project | rm -rf node_modules/
```

## Requirements

- [jq](https://jqlang.github.io/jq/) installed and on PATH
- Bash (Linux, macOS, or WSL)

# Pre-Tool-Use Hook — Block Destructive Commands

A Claude Code hook that intercepts dangerous bash commands before they execute.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -r` | Recursive file deletion |
| `DROP TABLE` / `DROP DATABASE` | Destroys DB objects |
| `TRUNCATE` | Deletes all table rows |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `git push --force` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted changes |
| `git clean -fd` | Deletes untracked files |
| `mkfs.*` | Formats filesystem |
| `shutdown` / `reboot` | System power commands |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use-hook.sh https://raw.githubusercontent.com/Ljm520/claude-builders-bounty/main/bounties/block-destructive-commands/pre-tool-use-hook.sh
chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
```

Then add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["~/.claude/hooks/pre-tool-use-hook.sh"]
      }
    ]
  }
}
```

## How It Works

1. Claude Code sends the bash command as JSON to the hook via stdin
2. Hook checks the command against destructive patterns
3. If blocked: logs to `~/.claude/hooks/blocked.log` and returns a `block` decision
4. If safe: exits cleanly, command proceeds

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-30T10:15:30+08:00] BLOCKED: rm -rf (recursive force delete) | COMMAND: rm -rf /tmp/project | PWD: /home/user
```

## What It Doesn't Do

- Doesn't block normal commands (`ls`, `cat`, `git add`, `npm install`, etc.)
- Doesn't modify any commands — it only blocks or allows
- Doesn't require any dependencies beyond bash and python3 (for JSON parsing)

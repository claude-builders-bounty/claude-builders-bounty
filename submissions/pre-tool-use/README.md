# pre-tool-use — Dangerous Command Blocker

Claude Code hook that intercepts dangerous bash commands before execution.

## Install (2 commands)

```bash
cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Then add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/pre-tool-use"
      }]
    }]
  }
}
```

## Blocked Patterns

| Pattern | Risk |
|---------|------|
| `rm -rf` | Recursive force delete |
| `git push --force` | Force push |
| `DROP TABLE` / `DROP DATABASE` | Database destruction |
| `DELETE FROM` (without WHERE) | Full table delete |
| `TRUNCATE` | Table data wipe |
| `chmod 777` | Overly permissive |
| `dd if=... of=/dev/...` | Raw disk write |
| `:(){ :|:& };:` | Fork bomb |

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

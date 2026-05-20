# safe-bash.py — Claude Code Pre-Tool-Use Hook

## 2-Command Installation

```bash
mkdir -p ~/.claude/hooks && cp safe-bash.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/safe-bash.py
```

Then add to Claude Code config (`~/.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/safe-bash.py"}]
    }]
  }
}
```

## Blocked Patterns

| Pattern | Examples |
|---------|----------|
| `rm -rf` | `rm -rf /`, `rm -r -f *` |
| `DROP TABLE` / `DROP DATABASE` | SQL destruction |
| `TRUNCATE` | Table truncation |
| `DELETE FROM` without WHERE | Full table wipe |
| `git push --force` / `-f` | Force push to remote |
| `chmod 777` on system dirs | Permission escalation |
| Fork bombs | `:(){ :\|:& };:` |

## Logs

`~/.claude/hooks/blocked.log` — timestamped records of every blocked attempt.

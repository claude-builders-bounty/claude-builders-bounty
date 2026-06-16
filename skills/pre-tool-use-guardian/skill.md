# Pre-Tool-Use Guardian

A Claude Code hook that blocks destructive bash commands before they execute.

## Usage

Install in `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 .claude/guardian.py"}]
      }
    ]
  }
}
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Destructive deletion |
| `rm -rf ~` | Home directory wipe |
| `git push --force` | Force push (asks confirmation) |
| `DROP TABLE` / `DROP DATABASE` | Database destruction |
| `chmod 777` | Insecure permissions |
| `curl ... | sh` (untrusted domains) | Pipeline injection |
| `.env` file reads/writes | Secret exposure |
| `sudo` (in most contexts) | Privilege escalation |

## Behavior

1. **Block**: Immediately deny with explanation
2. **Warn**: Ask for explicit confirmation
3. **Allow**: Let through silently
4. Logs all blocked attempts to `.claude/guardian.log`

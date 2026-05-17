# Bash Guard 🔒

A Claude Code PreToolUse hook that blocks destructive bash commands before they execute.

## Installation (2 steps)

**Step 1 — Copy the hook:**
```bash
mkdir -p .claude/hooks && cp skills/bash-guard/hook.py .claude/hooks/hook.py
```

**Step 2 — Register the hook:**
```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/hook.py",
            "args": [],
            "timeout": 10,
            "statusMessage": "Running bash guard..."
          }
        ]
      }
    ]
  }
}
```

Done. Destructive commands are now blocked automatically.

## What Gets Blocked

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm -r -f` | Irreversible recursive force delete |
| `DROP TABLE` | Destroys a database table and all data |
| `TRUNCATE <table>` | Wipes all rows from a table |
| `DELETE FROM <table>` (no WHERE/LIMIT) | Deletes all rows without recovery |
| `git push --force` / `git push -f` | Destroys remote history for others |
| `dd if=... of=/dev/...` | Can corrupt disks or partitions |

## Behaviour

- **Blocked commands** are rejected with a clear explanation shown to Claude
- **Every blocked attempt** is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
- **Normal commands** pass through without interference
- **Non-Bash tools** (Read, Write, Edit, etc.) are never blocked

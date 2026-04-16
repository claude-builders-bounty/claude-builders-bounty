# Claude Code Destructive Command Guard

A `pre-tool-use` hook for Claude Code that blocks dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp destructive_hook.py ~/.claude/hooks/pre-tool-use/destructive_guard.py
chmod +x ~/.claude/hooks/pre-tool-use/destructive_guard.py
```

Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use/destructive_guard.py"}]
      }
    ]
  }
}
```

## Blocked Commands

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE` | SQL table clear |
| `DELETE FROM` without `WHERE` | Bulk SQL delete |
| `git push --force` / `-f` | Force push (overwrites history) |
| `dd if=` | Disk write operations |
| `chmod -R 777` | Insecure permissions |
| `sudo rm` | Root-level delete |
| Fork bombs `:(){ :|:& }` | System resource exhaustion |

## How It Works

The hook reads Claude Code's `pre-tool-use` JSON from stdin, checks the `Bash` tool's command against blocked patterns using regex, and returns `{"action": "block", "message": "..."}` to prevent execution.

# Pre-Tool-Use Safety Hook for Claude Code

A Python hook that intercepts dangerous bash commands before Claude executes them.

## Setup (3 steps)

1. Copy to hooks directory:
   ```bash
   mkdir -p ~/.claude/hooks
   cp dangerous_commands.py ~/.claude/hooks/
   chmod +x ~/.claude/hooks/dangerous_commands.py
   ```

2. Add to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [{
             "type": "command",
             "command": "python3 ~/.claude/hooks/dangerous_commands.py"
           }]
         }
       ]
     }
   }
   ```

3. Done — Claude will now be blocked from running dangerous commands.

## What Gets Blocked

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE table` | SQL table truncation |
| `DELETE FROM` without WHERE | Wipes entire table |
| `git push --force` / `-f` | Force push overwrites history |
| `mkfs` | Formats filesystem |
| `dd if=... of=/dev/...` | Writes directly to device |

## Logs

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-27T10:30:00] BLOCKED: rm -rf: recursive force delete
  Command: rm -rf /var/data
  Project: /Users/tommy/my-project
```

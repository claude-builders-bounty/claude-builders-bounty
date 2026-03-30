# Pre-Tool-Use Hook: Block Destructive Bash Commands

This hook intercepts Claude Code's `Bash` tool and automatically blocks potentially catastrophic operations such as `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, and `DELETE FROM` without a `WHERE` clause.

It writes an audit log of every blocked attempt to `~/.claude/hooks/blocked.log` with the exact timestamp and working directory.

## Installation

1. Copy the script to Claude Code's hook folder and make it executable:
   ```bash
   mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
   ```

2. Add the hook to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/hooks/block-destructive.py"
             }
           ],
           "description": "Block destructive database and shell commands"
         }
       ]
     }
   }
   ```

## Logs

When a command is blocked, Claude receives an error explaining why it was blocked. You can view the full audit trail at:
```bash
cat ~/.claude/hooks/blocked.log
```

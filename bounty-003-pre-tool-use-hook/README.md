# Claude Code Pre-Tool-Use Hook: Block Destructive Bash

A `pre-tool-use` hook that intercepts destructive bash commands **before** they are executed by Claude Code. Blocks `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, and un-scoped `DELETE FROM`, logging every blocked attempt.

## How it works

| Pattern | Decision |
|---|---|
| `rm -rf <path>` / `rm -fr` | 🔴 **block** |
| `DROP TABLE <x>` | 🔴 **block** |
| `TRUNCATE [TABLE] <x>` | 🔴 **block** |
| `DELETE FROM <x>` without `WHERE` | 🔴 **block** |
| `git push --force` / `git push -f` | 🔴 **block** |
| `DELETE FROM ... WHERE ...` (scoped) | 🟢 allow |
| `git push` (normal) | 🟢 allow |
| `rm file.log` (no `-r`) | 🟢 allow |

## Install (3 steps)

1. `mkdir -p ~/.claude/hooks/pre_tool_use && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use/ && chmod +x ~/.claude/hooks/pre_tool_use/pre_tool_use.py`
2. Add the hook to your settings file (`~/.claude/settings.json` or project `.claude/settings.json`):
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/hooks/pre_tool_use/pre_tool_use.py"
             }
           ]
         }
       ]
     }
   }
   ```
3. Restart Claude Code. Every destructive command is now guarded.

## Logging

Every blocked attempt appends a line to `~/.claude/hooks/blocked.log`:

```
<UTC ISO-8601 timestamp> | reason=<matched pattern> | cwd=<project path> | cmd=<attempted command>
```

## Verified

Tested against 11 input cases: 7 destructive patterns blocked (exit 2), 4 safe commands allowed (exit 0). Test harness and full output are included in the PR.
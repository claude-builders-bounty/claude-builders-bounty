# pre-tool-use-hook.py — Destructive Command Blocker

Claude Code pre-tool-use hook that intercepts dangerous bash commands.

## Setup (1 command)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use-hook.py ~/.claude/hooks/
```

## Features

**Blocks these patterns:**
- `rm -rf` — recursive force remove
- `DROP TABLE` / `DROP DATABASE` — database destruction
- `git push --force` / `git push -f` — remote history overwrite
- `TRUNCATE` — deletes all table rows
- `DELETE FROM` without `WHERE` — mass row deletion
- `chmod 777` — world-writable permissions
- Fork bombs (`:(){ :|:& };:`)
- Direct disk writes (`> /dev/sda`)

**Logging:** Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp and project path.

**Does NOT interfere** with normal bash commands (`echo`, `git status`, `ls`, etc.)

## Configuration

Add to `~/.claude/claude_settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "bash|terminal|RunShellCommand|execute_command",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use-hook.py"
          }
        ]
      }
    ]
  }
}
```

## Testing

```bash
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' | python3 pre-tool-use-hook.py
# → {"continue": false, "reason": "⚠️ BLOCKED: Dangerous command detected..."}
```

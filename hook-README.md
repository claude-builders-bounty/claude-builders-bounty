# Destructive Command Hook for Claude Code

Blocks dangerous bash commands before Claude Code executes them.

## What it blocks
- `rm -rf` — recursive force delete
- `DROP TABLE` / `DROP DATABASE` — database destruction  
- `git push --force` — overwrites remote history
- `DELETE FROM` without WHERE — mass data deletion
- `chmod 777` — world-writable permissions
- `dd`, `/dev/sd*` writes — direct disk operations
- `reboot` / `shutdown` — system control
- `kill -9` — forced process kill

## Installation (2 commands)

```bash
# 1. Copy the hook script
cp destructive-command-hook.py ~/.claude/hooks/

# 2. Add to ~/.claude/hooks.json:
```

Add this to your `~/.claude/hooks.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "bash|terminal|execute_command",
        "command": "python3 ~/.claude/hooks/destructive-command-hook.py"
      }
    ]
  }
}
```

Or run this one-liner:

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/destructive-command-hook.py && python3 -c "
import json, os
hooks_path = os.path.expanduser('~/.claude/hooks.json')
hooks = {}
if os.path.exists(hooks_path):
    with open(hooks_path) as f: hooks = json.load(f)
hooks['hooks'] = hooks.get('hooks', {})
hooks['hooks']['pre-tool-use'] = [{'matcher': 'bash|terminal|execute_command', 'command': 'python3 ~/.claude/hooks/destructive-command-hook.py'}]
with open(hooks_path, 'w') as f: json.dump(hooks, f, indent=2)
print('✅ Hook installed!')
"
```

## Blocked attempts log
All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Testing
```bash
# This should be blocked:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/test"}' | python3 destructive-command-hook.py

# This should be allowed:
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"},"cwd":"/test"}' | python3 destructive-command-hook.py
```

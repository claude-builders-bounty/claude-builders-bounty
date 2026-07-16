# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# 1. Copy hook to Claude hooks directory
cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use_block_destructive.py

# 2. Register in settings (merge with existing ~/.claude/settings.json)
python3 -c "
import json, pathlib
s = pathlib.Path.home() / '.claude' / 'settings.json'
d = json.loads(s.read_text()) if s.exists() else {}
d.setdefault('hooks', {}).setdefault('pre_tool_use', []).append({
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/pre_tool_use_block_destructive.py'}]
})
s.write_text(json.dumps(d, indent=2))
print('Hook registered!')
"
```

## What It Blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, `mkfs`, `dd of=/dev/`, `shred` |
| **Database** | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (without WHERE) |
| **Git** | `git push --force`, `git reset --hard`, `git clean -fd` |
| **System** | `shutdown`, `reboot`, `halt`, fork bombs |
| **Permissions** | `chmod 000`, `chown -R / ` |
| **Overwrites** | Redirects to `/etc/`, `/boot/`, `/sys/` |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:
```
[2026-07-16T12:00:00Z] BLOCKED | project=/my/project | reason=rm -rf: Recursive force delete | command=rm -rf /
```

## How It Works

1. Claude Code calls a Bash tool
2. Hook receives JSON with `tool_name` and `tool_input.command`
3. Command is checked against 20+ destructive patterns
4. If blocked: returns `{"decision": "block", "reason": "..."}` + exit code 2
5. If allowed: exits with code 0 (command proceeds normally)

## Testing

```bash
# Test with a destructive command
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}' | python3 hooks/pre_tool_use_block_destructive.py
# Expected: JSON output with "decision": "block"

# Test with a safe command
echo '{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}' | python3 hooks/pre_tool_use_block_destructive.py
# Expected: no output, exit code 0
```

# Block Destructive Bash Commands Hook

A Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## What it blocks

- `rm -rf` / `rm -fr` style recursive force deletion
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

## Installation

From this directory, install the hook in two commands:

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json
from pathlib import Path
settings_path = Path.home() / '.claude' / 'settings.json'
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
hooks = settings.setdefault('hooks', {})
pre = hooks.setdefault('PreToolUse', [])
entry = {
    'matcher': 'Bash',
    'hooks': [
        {
            'type': 'command',
            'command': 'python3 ~/.claude/hooks/block_destructive_bash.py'
        }
    ]
}
if entry not in pre:
    pre.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + '\n')
PY
```

## How it works

Claude Code sends hook payloads as JSON on stdin. The script reads the payload,
extracts the Bash command from `tool_input.command`, and exits:

- `0` for safe commands, allowing Bash to run
- `2` for blocked commands, preventing Bash execution and displaying the reason

## Manual check

```bash
printf '{"tool_input":{"command":"rm -rf dist"}}' | python3 pre_tool_use.py
# exits 2 and writes ~/.claude/hooks/blocked.log

printf '{"tool_input":{"command":"ls -la"}}' | python3 pre_tool_use.py
# exits 0
```

# Destructive Command Guard Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
hook_command = f"python3 {Path.home() / '.claude' / 'hooks' / 'destructive_command_guard.py'}"
pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
pre_tool_use[:] = [
    item for item in pre_tool_use
    if not any(hook.get("command") == hook_command for hook in item.get("hooks", []))
]
pre_tool_use.append({
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": hook_command
    }]
})
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

## What It Blocks

- `rm -rf`, `rm -fr`, `rm -r -f`, and `rm --recursive --force`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with timestamp, attempted command, project path, and reason.

## Verify

```bash
python3 -m unittest tests/test_destructive_command_guard.py
```

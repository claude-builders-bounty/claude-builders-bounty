# Destructive Command Blocker Hook

This Claude Code `PreToolUse` hook blocks high-risk Bash commands before they run and records every blocked attempt in `~/.claude/hooks/blocked.log`.

## What It Blocks

- `rm -rf` and equivalent combined recursive-force `rm` flags
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL statements containing `DROP TABLE`
- SQL statements containing `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Normal Bash commands are allowed through unchanged.

## Install In 2 Commands

```bash
mkdir -p ~/.claude/hooks && cp destructive_command_blocker.py ~/.claude/hooks/destructive_command_blocker.py && chmod +x ~/.claude/hooks/destructive_command_blocker.py
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
entry = {
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": str(Path.home() / ".claude" / "hooks" / "destructive_command_blocker.py")
    }]
}
pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
if entry not in pre_tool_use:
    pre_tool_use.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

## Test Manually

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}' | ~/.claude/hooks/destructive_command_blocker.py
echo $?
```

The first command should print a clear block reason and the exit code should be `2`, which tells Claude Code to stop the Bash tool call.

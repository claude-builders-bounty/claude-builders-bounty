# Destructive Command Guard Hook

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run. It denies:

- `rm -rf` and equivalent recursive-force `rm` forms, including common wrappers like `sudo rm -rf` and `bash -c 'rm -rf ...'`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL statements containing `DROP TABLE`, `TRUNCATE`, or `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended as JSON lines to `~/.claude/hooks/blocked.log` with a UTC timestamp, attempted command, project path, and block reason.

## Install

From this directory:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py && chmod +x ~/.claude/hooks/destructive_command_guard.py
```

```bash
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
hooks = settings.setdefault("hooks", {})
entry = {
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": str(Path.home() / ".claude" / "hooks" / "destructive_command_guard.py"),
    }],
}
pre_tool_use = hooks.setdefault("PreToolUse", [])
if entry not in pre_tool_use:
    pre_tool_use.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY
```

The second command adds the hook to `~/.claude/settings.json`. A minimal settings example is also available in `examples/settings.json`.

## How It Works

Claude Code sends the proposed tool call to the hook on stdin. For non-Bash tools, malformed input, or ordinary Bash commands, the hook exits successfully without output. For a blocked Bash command, it logs the attempt and returns a `permissionDecision: "deny"` response with a clear reason for Claude.

## Test

```bash
python3 tests/test_destructive_command_guard.py
```

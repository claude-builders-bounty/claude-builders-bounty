# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook for the Bash tool. It blocks high-risk commands before they run and records each blocked attempt in `~/.claude/hooks/blocked.log`.

## What It Blocks

- `rm -rf` and `rm -fr`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Normal Bash commands exit with no output and are allowed.

## Install

Run these two commands from this repository:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive_bash_guard.py ~/.claude/hooks/destructive_bash_guard.py
```

```bash
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
settings.setdefault("hooks", {}).setdefault("PreToolUse", []).append({
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/destructive_bash_guard.py"
    }]
})
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

## Example

Given this Claude Code hook input:

```json
{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build"},"cwd":"/repo"}
```

The hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked `rm -rf`: recursive force removal is destructive."
  }
}
```

The blocked attempt is also appended to:

```text
~/.claude/hooks/blocked.log
```

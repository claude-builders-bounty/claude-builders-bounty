# Destructive Command PreToolUse Hook

This Claude Code `PreToolUse` hook blocks dangerous Bash commands before they run.

It blocks:

- `rm -rf` and equivalent recursive forced `rm` variants
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements that do not include `WHERE`

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- `timestamp`
- `command`
- `project_path`
- `reason`

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook/pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_blocker.py"
        }
    ]
}
if entry not in pre_tool_use:
    pre_tool_use.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

That is the full installation: one copy command and one settings update command.

## Example Block Response

When Claude Code attempts `rm -rf ./dist`, the hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny"
  },
  "systemMessage": "Blocked `rm -rf`: recursive forced deletion can remove large parts of the filesystem..."
}
```

Normal Bash commands return `{}` and continue without interruption.

## Run Tests

```bash
python3 destructive-command-hook/test_pre_tool_use_blocker.py
```

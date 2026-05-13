# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that blocks destructive Bash commands before
they run.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON
Lines with:

- timestamp
- blocked pattern
- attempted command
- project path

## Install

Run these two commands from this repository:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-blocker.py ~/.claude/hooks/pre-tool-use-blocker.py && chmod +x ~/.claude/hooks/pre-tool-use-blocker.py
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
settings["hooks"]["PreToolUse"].append({
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": str(Path.home() / ".claude" / "hooks" / "pre-tool-use-blocker.py")
    }]
})
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

## How It Works

Claude Code sends hook input as JSON on stdin. The hook only inspects Bash tool
calls, reads `tool_input.command`, and exits normally for safe commands. When a
blocked pattern is found, it logs the attempt and returns a `PreToolUse` deny
decision with a clear reason for Claude.

Example denied output:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command..."
  }
}
```

## Manual Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' \
  | ~/.claude/hooks/pre-tool-use-blocker.py
```

Safe commands produce no output and exit successfully:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/tmp/project"}' \
  | ~/.claude/hooks/pre-tool-use-blocker.py
```

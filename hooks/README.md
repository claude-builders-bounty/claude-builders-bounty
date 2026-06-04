# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
settings = pathlib.Path.home() / ".claude" / "settings.json"
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": str(pathlib.Path.home() / ".claude" / "hooks" / "block_destructive_bash.py"),
        "args": []
    }]
})
settings.parent.mkdir(parents=True, exist_ok=True)
settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM <table>` without a `WHERE` clause

Normal Bash commands exit silently and continue through Claude Code's usual permission flow.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each line includes a UTC timestamp, the project path, the matched dangerous pattern, and the attempted command.

## Manual test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/project"}' \
  | python3 hooks/block_destructive_bash.py
```

Expected output contains:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command ..."
  }
}
```

Safe commands produce no output and return exit code `0`:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"npm test"}}' \
  | python3 hooks/block_destructive_bash.py
```

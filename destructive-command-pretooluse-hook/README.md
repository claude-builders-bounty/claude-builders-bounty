# Destructive Command PreToolUse Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

The hook returns the current Claude Code structured decision format:
`hookSpecificOutput.hookEventName=PreToolUse`,
`hookSpecificOutput.permissionDecision=deny`, and
`hookSpecificOutput.permissionDecisionReason=<clear explanation>`.

## Install

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_destructive_guard.py ~/.claude/hooks/pre_tool_use_destructive_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_destructive_guard.py
```

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
settings = json.loads(p.read_text()) if p.exists() else {}
settings.setdefault("hooks", {})["PreToolUse"] = [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use_destructive_guard.py"}]}]
p.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

## Blocks

- `rm -rf` and equivalent combined flags like `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Safe commands like `git status`, `rm file.txt`, `git push --force-with-lease`, and `DELETE FROM table WHERE id = 1` are allowed.

## Test

```bash
python3 -m unittest discover destructive-command-pretooluse-hook -p "test_*.py"
```

Manual blocked-command check:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf dist"},"cwd":"%s"}' "$PWD" | python3 pre_tool_use_destructive_guard.py
```

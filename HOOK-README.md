# Destructive Command Guard for Claude Code

A zero-dependency Claude Code `PreToolUse` hook that blocks high-risk Bash commands before Claude Code runs them.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-guard.py ~/.claude/hooks/destructive-command-guard.py && chmod +x ~/.claude/hooks/destructive-command-guard.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text() or "{}") if p.exists() else {}
hooks = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/destructive-command-guard.py"}]}
if entry not in hooks:
    hooks.append(entry)
p.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## What it blocks

- `rm -rf` / `rm -fr` recursive forced deletes
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

## Behavior

- Reads Claude Code hook JSON from `stdin`.
- Only inspects Bash tool calls; non-Bash tools are ignored.
- Safe Bash commands exit `0` with no output, so they proceed normally.
- Blocked commands return Claude Code's structured PreToolUse denial output:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command..."
  }
}
```

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Log entries are JSON Lines and include:

- UTC timestamp
- attempted command
- project path / cwd
- block reason

## Quick local test

```bash
python3 test_destructive_command_guard.py
```

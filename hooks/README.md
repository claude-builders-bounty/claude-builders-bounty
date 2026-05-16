# Block Destructive Bash Commands Hook

This Claude Code `PreToolUse` hook blocks dangerous Bash commands before they run.

It blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, project path, and reason.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text() if p.exists() else "{}")
data.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_bash.py"}]}
if entry not in data["hooks"]["PreToolUse"]:
    data["hooks"]["PreToolUse"].append(entry)
p.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## Quick Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/example"},"cwd":"/tmp/project"}' | python3 ~/.claude/hooks/block_destructive_bash.py
```

The hook exits with code `2`, writes a clear block reason to stderr, and logs the attempt.

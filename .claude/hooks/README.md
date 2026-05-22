# Destructive Bash Guard

This Claude Code `PreToolUse` hook blocks dangerous Bash commands before they run:

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with a timestamp, command, project path, and reason.

The project-level hook configuration is included in `.claude/settings.json`. Copy the `.claude` directory into a project to enable the guard for that project, or install the script globally with the commands below.

## Install

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text() or "{}") if p.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_bash.py"}],
})
p.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## Quick Check

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build"},"cwd":"/tmp/project"}' | python3 .claude/hooks/block_destructive_bash.py
```

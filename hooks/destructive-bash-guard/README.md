# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they
run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-bash-guard/block_destructive_bash.py ~/.claude/hooks/
```

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
data = json.loads(p.read_text()) if p.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({
  "matcher": "Bash",
  "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_bash.py"}],
})
p.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## What It Blocks

- `rm -rf`, including equivalent flag order such as `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Normal Bash commands are allowed. Non-Bash tools are ignored.

## Logging

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON and includes:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Manual Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build","cwd":"/tmp/project"}}' \
  | python3 hooks/destructive-bash-guard/block_destructive_bash.py
```

The output contains a `permissionDecision` of `deny` and a clear reason for
Claude.

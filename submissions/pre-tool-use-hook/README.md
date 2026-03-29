# Pre-Tool-Use Hook: Destructive Command Blocker

A Claude Code pre-tool-use hook that silently intercepts dangerous bash and SQL commands before they execute, logs every blocked attempt, and explains to Claude why the command was stopped.

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` | Recursive forced deletion — irreversible |
| `git push --force` / `git push -f` | Overwrites remote history |
| `DROP TABLE` | Permanently destroys a database table |
| `TRUNCATE` | Removes all rows from a table without rollback |
| `DELETE FROM` without `WHERE` | Deletes every row in a table |

Safe commands (e.g. `ls`, `DELETE FROM ... WHERE id=1`) pass through unchanged.

## Installation (2 commands)

```bash
cp hook.py ~/.claude/hooks/pre-tool-use-hook.py && chmod +x ~/.claude/hooks/pre-tool-use-hook.py
```

```bash
python3 - <<'EOF'
import json, os
cfg = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(cfg), exist_ok=True)
data = {}
try:
    with open(cfg) as f: data = json.load(f)
except FileNotFoundError:
    pass
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use-hook.py"}]
})
with open(cfg, "w") as f: json.dump(data, f, indent=2)
print("Hook registered in", cfg)
EOF
```

## How it works

Claude Code calls pre-tool-use hooks before any tool runs. This hook:

1. Reads the JSON payload (`tool_name` + `tool_input`) from **stdin**
2. If `tool_name` is `Bash`, checks the command against dangerous regex patterns
3. Returns `{"action": "block", "message": "..."}` to stop the command **or** `{"action": "allow"}` to let it proceed
4. Appends a structured entry to `~/.claude/hooks/blocked.log` for every blocked attempt

### Log format

```
[2026-03-29T12:00:00+00:00] BLOCKED | reason='rm -rf: recursive forced file deletion' | cwd='/home/user/project' | command='rm -rf /'
```

## Manual test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' \
  | python3 ~/.claude/hooks/pre-tool-use-hook.py
```

Expected output:

```json
{"action": "block", "message": "BLOCKED by pre-tool-use safety hook.\nReason: rm -rf: recursive forced file deletion\n..."}
```

## Requirements

- Python 3.7+
- No third-party dependencies (stdlib only)

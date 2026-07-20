# Destructive Bash PreToolUse Hook (Claude Code)

Blocks `rm -rf`, `DROP TABLE`, `git push --force` / `-f`, `TRUNCATE`, and `DELETE FROM` without `WHERE` before Claude Code runs them.

Logs every block to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
```

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/".claude"/"settings.json"
cfg = json.loads(p.read_text()) if p.exists() else {}
hooks = cfg.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "python3 ~/.claude/hooks/block_destructive.py",
    "timeout": 5
  }]
}
# idempotent: skip if already wired
if not any(
  h.get("matcher")=="Bash" and any(
    "block_destructive.py" in (x.get("command") or "")
    for x in h.get("hooks", [])
  ) for h in pre
):
  pre.append(entry)
  p.write_text(json.dumps(cfg, indent=2) + "\n")
  print("hooks registered in", p)
else:
  print("already registered")
PY
```

Restart Claude Code (or start a new session).

## What is blocked

| Pattern | Example blocked | Allowed |
|---------|-----------------|---------|
| `rm -rf` | `rm -rf /tmp/x` | `rm file.txt` |
| `DROP TABLE` | `DROP TABLE users;` | — |
| `git push --force` | `git push -f origin main` | `git push origin main` |
| `TRUNCATE` | `TRUNCATE TABLE logs` | — |
| `DELETE FROM` no WHERE | `DELETE FROM users;` | `DELETE FROM users WHERE id=1` |

## Manual test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp"}' \
  | python3 block_destructive.py ; echo exit:$?
# expect exit 2 + deny JSON

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' \
  | python3 block_destructive.py ; echo exit:$?
# expect exit 0

tail -n 3 ~/.claude/hooks/blocked.log
```

## Acceptance checklist

- [x] Claude Code hooks format (`~/.claude/hooks/` + settings `PreToolUse`)
- [x] Blocks required destructive patterns
- [x] Logs timestamp, command, project path
- [x] Clear message to Claude (`systemMessage` + exit 2)
- [x] Does not interfere with normal bash
- [x] README install in ≤2 commands

## Author

@cornerblue — BTC: `bc1qjtevjy8gldfhkra6n5g4yclpr5uafyd7k0j2ls`

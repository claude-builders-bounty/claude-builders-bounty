# block_destructive — Claude Code Safety Hook

A `pre-tool-use` hook for Claude Code that intercepts dangerous bash commands
**before** they execute and logs every blocked attempt.

## Install (2 commands)

```bash
curl -fsSL https://raw.githubusercontent.com/Ishant5436/claude-builders-bounty/main/submissions/bounty-3-ishant/block_destructive.py \
  -o ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py
```

Then add the hook to `~/.claude/settings.json`:

```bash
python3 - <<'EOF'
import json, os
path = os.path.expanduser("~/.claude/settings.json")
cfg = json.load(open(path)) if os.path.exists(path) else {}
cfg.setdefault("hooks", {}).setdefault("PreToolUse", []).append({
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive.py"}]
})
json.dump(cfg, open(path, "w"), indent=2)
print("Hook registered.")
EOF
```

That's it — Claude is now protected.

---

## Blocked patterns

| Pattern | Reason |
|---|---|
| `rm -rf` / `rm -Rf` / `rm -fr` | Recursive force deletion |
| `git push --force` / `git push -f` | Destructive remote history rewrite |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | Permanent data destruction |
| `TRUNCATE` | Removes all rows without a WHERE clause |
| `DELETE FROM` **without** `WHERE` | Deletes every row in the table |

Safe variants are **allowed**:
- `DELETE FROM users WHERE id = 1` ✅
- `git push origin main` ✅
- `rm -r /tmp/build` ✅ (recursive but not force)

---

## Log format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as a
newline-delimited JSON record:

```json
{"timestamp": "2026-06-04T10:22:01+00:00", "reason": "rm -rf: recursive force deletion", "project_path": "/Users/me/myproject", "command": "rm -rf /"}
```

---

## How it works

Claude Code invokes the hook **before** each `Bash` tool call, piping a JSON
payload to stdin:

```json
{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "project_path": "/..."}
```

The hook exits with code `2` and prints a JSON block decision to stdout to
block the command, or exits `0` to allow it. Claude receives the block reason
and explains the refusal to the user.

---

## Requirements

- Python 3.8+
- Claude Code with hooks support (`~/.claude/settings.json`)

## License

MIT

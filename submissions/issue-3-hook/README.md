# Claude Code — Destructive Command Blocker

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they execute, with structured logging of every blocked attempt.

## Setup (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/
```

Then add the hook to your Claude Code settings:

```bash
python - <<'EOF'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg.setdefault("hooks", {}).setdefault("pre-tool-use", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": f"python {pathlib.Path.home()}/.claude/hooks/block_destructive.py"}]}
if entry not in cfg["hooks"]["pre-tool-use"]:
    cfg["hooks"]["pre-tool-use"].append(entry)
p.write_text(json.dumps(cfg, indent=2))
print("Hook registered.")
EOF
```

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete with no recovery |
| `DROP TABLE` | Permanently destroys a DB table |
| `TRUNCATE` | Empties a table with no rollback |
| `DELETE FROM` without `WHERE` | Deletes every row |
| `git push --force` | Overwrites remote history |
| `git reset --hard` | Discards all uncommitted changes |
| `chmod 777` | World-writable permissions (security risk) |
| `dd if=... of=/dev/` | Direct device write — can wipe disks |
| Fork bomb `:(){ :|:& }` | Crashes system via process exhaustion |

## Logs

Every blocked attempt is written to `~/.claude/hooks/blocked.log`:

```
[2026-05-20T14:32:01Z] BLOCKED | project='/home/user/myapp' | reason='Recursive force delete...' | command='rm -rf ./dist'
```

## How It Works

Claude Code runs this script before every `Bash` tool call. The script receives a JSON payload on stdin:

```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf /" }
}
```

- Exit `0` → command is allowed
- Exit `2` → command is blocked; stderr message shown to Claude and the user

Normal bash commands are completely unaffected. Only the patterns above trigger a block.

## Running Without Claude Code (testing)

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python block_destructive.py
```

You should see the block message and exit code 2.

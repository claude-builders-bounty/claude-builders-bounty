# pre-tool-use safety hook for Claude Code

Blocks dangerous bash commands before Claude executes them.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
```

Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py" }]
      }
    ]
  }
}
```

## What it blocks

| Pattern | Reason |
|---|---|
| `rm -rf` / `rm -fr` | Recursive force delete |
| `DROP TABLE` | Destructive SQL |
| `TRUNCATE` | Destructive SQL |
| `DELETE FROM` without `WHERE` | Wipes entire table |
| `git push --force` (not `--force-with-lease`) | Rewrites remote history |

## Log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
2026-06-19T10:22:05 | BLOCKED | cmd='rm -rf node_modules' | reason=rm -rf: recursive force delete | project=/home/user/myapp
```

## How it works

Claude Code calls the hook via stdin with a JSON payload before executing any `Bash` tool call. The hook reads the command, checks it against the pattern list, and either:
- Exits 0 silently → command proceeds
- Prints `{"decision": "block", "reason": "..."}` → Claude sees the reason and stops

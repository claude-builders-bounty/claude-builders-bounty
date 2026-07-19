# Bounty #3 — Pre-tool-use Hook: Block Destructive Bash Commands ($100)

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands
before Claude executes them.

## Files

- `hooks/block-destructive.py` — the logic (Python 3, stdlib only)
- `hooks/pre-tool-use.sh` — bash wrapper that forwards stdin to the Python script
- `README.md` — this file

## Install

```bash
mkdir -p ~/.claude/hooks
cp hooks/block-destructive.py hooks/pre-tool-use.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

Add to `~/.claude/settings.json` (or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/pre-tool-use.sh" }
        ]
      }
    ]
  }
}
```

## Blocked patterns

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete — unrecoverable |
| `DROP TABLE` | Destroys a table |
| `git push --force` | Overwrites remote history |
| `TRUNCATE` | Empties a table |
| `DELETE FROM` without `WHERE` | Deletes all rows |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
2026-07-20T01:37:56 | project=/home/vps2 | reason=rm -rf (recursive force delete) | cmd=rm -rf /tmp/test
```

## How it works

Claude Code calls the hook before each Bash tool call with a JSON payload on
stdin (`tool_name`, `tool_input.command`, `cwd`). If the command matches a
dangerous pattern, the hook prints `{"decision":"block","reason":"..."}` and
exits `1`. Otherwise it exits `0` and Claude proceeds.

## Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/home/vps2"}' | python3 block-destructive.py
# → {"decision":"block",...}  exit 1

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/home/vps2"}' | python3 block-destructive.py
# → exit 0
```

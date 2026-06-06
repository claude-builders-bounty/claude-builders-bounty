# destructive-guard — Claude Code pre-tool-use hook

Blocks dangerous bash commands **before** Claude Code executes them. Every blocked attempt is logged with a timestamp and project path.

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` / `rm -fr` / `rm -Rf` (any order) | Recursive force-delete — wipes entire directories |
| `DROP TABLE` | Destroys a database table and all its data |
| `git push --force` / `git push -f` | Overwrites remote history; can't be undone |
| `TRUNCATE` | Empties a database table |
| `DELETE FROM` without `WHERE` | Deletes every row in a table |

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hook.py ~/.claude/hooks/pre-tool-use/destructive-guard.py
```

Then add the hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use/destructive-guard.py"
          }
        ]
      }
    ]
  }
}
```

## How it works

Claude Code passes tool-use input as JSON on stdin before execution. This hook:

1. Reads the JSON payload from stdin
2. Extracts the bash command from `tool_input.command`
3. Checks against destructive patterns using regex
4. If blocked: prints `{"decision": "block", "reason": "<message>"}` and exits with code 2
5. Logs every blocked attempt to `~/.claude/hooks/blocked.log`

Claude sees the block reason and can explain to the user why the command was prevented.

## Log format

```
2026-06-06T05:12:33Z | tool=Bash | reason=rm -rf (recursive force delete) | cmd='rm -rf /tmp/data' | project=/Users/you/myproject
```

## Running tests

```bash
python3 test_hook.py
# 15/15 tests passed
```

## Normal commands are not affected

```bash
rm -r ./build        # ✅ allowed (no -f flag)
rm -f /tmp/foo.txt   # ✅ allowed (single file, no -r)
git push origin main # ✅ allowed (no --force)
DELETE FROM logs WHERE ts < '2024-01-01';  # ✅ allowed (has WHERE)
ls -la               # ✅ allowed
```

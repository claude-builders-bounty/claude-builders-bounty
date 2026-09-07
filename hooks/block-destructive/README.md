# Block destructive bash (Claude Code PreToolUse hook)

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.py
```

Then merge this into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

## What it blocks

- `rm -rf` / `rm -fr`
- `git push --force` / `git push -f`
- `DROP TABLE`
- `TRUNCATE …`
- `DELETE FROM …` without a `WHERE` clause

Blocked attempts append a line to `~/.claude/hooks/blocked.log` with UTC timestamp, project path, reason, and command.

## Test locally

```bash
echo '{"tool_input":{"command":"rm -rf /tmp/demo"}}' | python3 block-destructive.py; echo exit:$?
echo '{"tool_input":{"command":"ls -la"}}' | python3 block-destructive.py; echo exit:$?
```

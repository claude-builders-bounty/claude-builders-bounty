# Pre-Tool-Use Security Hook

A Claude Code `pre-tool-use` hook that blocks destructive bash commands.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
curl -sL -o ~/.claude/hooks/pre-tool-use/block.py https://raw.githubusercontent.com/your-repo/main/block.py
chmod +x ~/.claude/hooks/pre-tool-use/block.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|ExecuteCommand",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/pre-tool-use/block.py"}
        ]
      }
    ]
  }
}
```

## Blocked

- `rm -rf`
- `DROP TABLE`/`DATABASE`/`SCHEMA`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM x` (no WHERE)

## Logs

`~/.claude/hooks/blocked.log`:
```
[2026-06-18T15:00:00] BLOCKED | Rule: rm -rf | Command: rm -rf / | Project: /home/user/proj
```

## License

MIT

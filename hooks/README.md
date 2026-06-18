# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that blocks destructive bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
curl -sL -o ~/.claude/hooks/pre-tool-use/block_destructive_commands.py https://raw.githubusercontent.com/your-repo/main/block_destructive_commands.py
chmod +x ~/.claude/hooks/pre-tool-use/block_destructive_commands.py
```

Then add to your Claude Code `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|ExecuteCommand",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` (recursive forced deletion) | Catastrophic data loss |
| `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA` | SQL data destruction |
| `git push --force`, `git push -f` | Overwrites remote history |
| `TRUNCATE TABLE` | SQL data destruction |
| `DELETE FROM x` (without WHERE) | Unconditional deletion |

## Testing

Run the test suite:

```bash
cd tests/
python3 -m pytest test_block_destructive_commands.py -v
```

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-18T15:00:00] BLOCKED | Rule: rm -rf recursive delete | Command: rm -rf / | Project: /home/user/project
```

## License

MIT

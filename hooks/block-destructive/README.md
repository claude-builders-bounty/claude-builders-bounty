# Block Destructive Commands — Claude Code PreToolUse Hook

Blocks dangerous bash and SQL commands before Claude Code executes them. Logs every block to `~/.claude/hooks/blocked.log`.

## Blocks

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` / `git push -f`
- `DELETE FROM <table>` without a `WHERE` clause

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive/block_destructive.py ~/.claude/hooks/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
```

Add to `~/.claude/settings.json` (or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "${HOME}/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 hooks/block-destructive/test_block_destructive.py
```

Closes claude-builders-bounty/claude-builders-bounty#3 ($100 Opire bounty).

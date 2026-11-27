# Claude Code Pre-Tool-Use Hook: Block Destructive Commands

Blocks destructive bash/git commands via Claude Code `pre-tool-use` hook.

## Install (2 commands)
1. Copy `block-destructive.py` to your Claude Code hooks directory as `pre-tool-use`.
2. Add to `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked patterns
- `rm -rf` / `rm -fr` / `rm -r -f` (recursive force delete)
- `git push --force` / `--force-with-lease` / `-f`
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE TABLE`, `DELETE FROM … without WHERE`

Exit code 2 blocks; exit 0 allows. Logs blocks to `~/.claude/hooks/blocked.log`.

## Test
Run `python3 test_hook.py` — 33 cases covering blocks, allows, and malformed input.

# Block destructive bash commands — Claude Code PreToolUse hook

Fixes claude-builders-bounty/claude-builders-bounty#3.

## What it blocks

- `rm -rf` (including `rm -fr`, `rm -rfv`, `sudo rm -rf`, `--recursive --force`)
- `DROP TABLE`
- `git push --force` (and `git push -f`)
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`
with timestamp, attempted command, and project path. Normal commands
pass through untouched.

## Install (2 commands)

```
mkdir -p ~/.claude/hooks && cp block-destructive-hook.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-hook.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-hook.py"
          }
        ]
      }
    ]
  }
}
```

## Verify

```
python3 test_hook.py
```

Expected: all blocked cases exit 2 with a clear reason and one log line
each; all normal commands exit 0 with no log line.
Verified locally: 12 blocked cases, 9 allowed cases, all tests passed.

# Block Destructive Bash Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
python3 hooks/block-destructive-bash/block_destructive_bash.py --install
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and registers it in `~/.claude/settings.json` for Bash `PreToolUse` events.

## What It Blocks

- `rm -rf`, `rm -fr`, and separated recursive/force variants
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE` and `TRUNCATE TABLE`
- `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- UTC timestamp
- attempted command
- project path
- block reason

## Claude Code Hook Format

The installer writes this hook entry if it is not already present:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

When a command is blocked, the hook returns a `permissionDecision: "deny"` response with a clear reason for Claude. Safe Bash commands exit quietly with status `0`.

## Test Locally

```bash
python3 -m unittest discover -s tests
```

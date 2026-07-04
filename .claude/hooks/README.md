# Destructive Bash Guard Hook

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they
run and logs each blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

From this repository:

```bash
python3 .claude/hooks/install.py
```

The installer copies `block_destructive_bash.py` into `~/.claude/hooks/` and
adds this `PreToolUse` matcher to `~/.claude/settings.json`:

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

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Normal Bash commands exit with code `0`. Blocked commands write a clear reason
to stderr and exit with code `2`, so Claude Code receives the denial message and
does not run the risky command.

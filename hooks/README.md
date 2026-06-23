# Destructive Bash Command Hook

This PreToolUse hook blocks common destructive Bash commands before Claude Code can run them.

## Install

1. Copy `.claude/hooks/block_destructive_bash.py` into `~/.claude/hooks/block_destructive_bash.py`.
2. Add this matcher to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

Blocked attempts are appended as JSON lines to `~/.claude/hooks/blocked.log`.

The hook denies `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` statements that do not include a `WHERE` clause. Other Bash commands pass through without output.

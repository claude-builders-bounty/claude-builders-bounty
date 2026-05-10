# Block Dangerous Bash Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block-dangerous-bash.py ~/.claude/hooks/
```

Add this hook entry to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-dangerous-bash.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

The hook blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, attempted command, matched pattern, and project path.

Normal Bash commands exit quietly and do not interfere with Claude Code.

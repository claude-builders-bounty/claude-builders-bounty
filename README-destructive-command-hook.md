# Destructive Command PreToolUse Hook

Blocks dangerous Bash commands before Claude Code can run them.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook.py ~/.claude/hooks/destructive-command-hook.py && chmod +x ~/.claude/hooks/destructive-command-hook.py
```

Add this hook to your Claude Code settings for Bash `PreToolUse` events:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/destructive-command-hook.py"
          }
        ]
      }
    ]
  }
}
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

Normal Bash commands exit `0` and pass through untouched.

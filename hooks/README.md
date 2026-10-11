# Destructive Bash command hook

This Claude Code `PreToolUse` hook blocks high-risk Bash commands before they run:

- `rm -rf` and equivalent recursive force removal
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended as one JSON line to `~/.claude/hooks/blocked.log` with its UTC timestamp, command, reason, and project path. Safe commands pass through unchanged.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

Add this command to the `PreToolUse` hook for the `Bash` tool in your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/block-destructive-bash.py" }] }
    ]
  }
}
```

The hook reads the standard Claude Code hook JSON from stdin. It exits `0` for allowed commands and exits `2` with a clear explanation when a destructive command is blocked.

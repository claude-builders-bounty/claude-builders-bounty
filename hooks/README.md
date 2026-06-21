# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they
run.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC
timestamp, the attempted command, the project path, and the matched rule.

Normal Bash commands exit successfully and are not logged.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add this hook to `~/.claude/settings.json`:

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

## Behavior

Claude Code sends tool-use payloads to the script on stdin. When the tool is not
`Bash`, or when the Bash command is safe, the hook exits `0`.

When a destructive pattern is detected, the hook:

1. writes the blocked attempt to `~/.claude/hooks/blocked.log`;
2. prints a clear explanation to stderr for Claude; and
3. exits `2` so the tool call is blocked before execution.

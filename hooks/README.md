# Destructive Bash Guard Hook

Claude Code `pre-tool-use` hook that blocks destructive bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

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

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with the timestamp, attempted command, project path, and matched reason.

## Manual Test

```bash
echo '{"tool_input":{"command":"rm -rf node_modules"},"cwd":"/tmp/project"}' | python3 hooks/block_destructive_bash.py
```

The command exits non-zero and prints a clear explanation. Normal commands such as `ls -la` exit with `0`.

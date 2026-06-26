# Destructive Bash PreToolUse Hook

This Claude Code hook blocks dangerous Bash commands before they run and logs
each blocked attempt to `~/.claude/hooks/blocked.log`.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks
cp destructive-bash-hook/.claude/hooks/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

Add this hook to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked patterns

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause
- `git push --force`, `git push --force-with-lease`, and `git push -f`

## Behavior

When a command is blocked, the hook exits with status `2`, writes a clear denial
message to stderr for Claude Code, and appends a JSON line to
`~/.claude/hooks/blocked.log` containing:

- timestamp
- attempted command
- project path
- block reason

## Test

```bash
python3 destructive-bash-hook/tests/test_block_destructive_bash.py
```


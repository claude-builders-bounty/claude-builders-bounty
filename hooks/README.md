# Destructive Bash Command Guard

`pre_tool_use_block_dangerous_bash.py` is a Claude Code `PreToolUse` hook
that blocks destructive Bash commands before they execute.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause
- `git push --force`

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC
timestamp, attempted command, block reason, and project path.

## Install

Run from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_block_dangerous_bash.py ~/.claude/hooks/pre_tool_use_block_dangerous_bash.py
chmod +x ~/.claude/hooks/pre_tool_use_block_dangerous_bash.py
```

Then add this hook entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_block_dangerous_bash.py"
          }
        ]
      }
    ]
  }
}
```

On Windows, replace `python3` with `python` if needed.

## Test

```bash
python -m unittest discover -s tests
```

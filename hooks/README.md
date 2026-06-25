# Destructive Bash Guard Hook

A Claude Code `PreToolUse` hook that blocks risky Bash commands before they run.

## Install

```bash
chmod +x hooks/install.sh
hooks/install.sh
```

The installer copies the hook to `~/.claude/hooks/` and prints the Claude Code settings block:

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
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` when no `WHERE` appears before the statement terminator

Blocked attempts are written as JSON lines to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes a timestamp, reason, attempted command, and project path.

## Validate

```bash
python3 tests/test_block_destructive_bash.py
```

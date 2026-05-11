# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they
run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/
```

```bash
python ~/.claude/hooks/block_destructive_bash.py --print-settings >> ~/.claude/settings.json
```

If `~/.claude/settings.json` already exists, merge the printed `hooks` object
instead of appending raw JSON.

## What It Blocks

- `rm -rf`, including equivalent flag order such as `rm -fr` or `rm -r -f`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL statements containing `DROP TABLE`
- SQL statements containing `TRUNCATE`
- `DELETE FROM ...` statements that do not include a `WHERE` clause before the
  next semicolon

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes an ISO timestamp, project path, reason, and attempted
command.

## Settings Snippet

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

## Test

```bash
python block_destructive_bash.py --self-test
```

The hook reads Claude Code hook JSON from stdin. Safe commands exit without
output. Blocked commands print a `PreToolUse` deny decision that explains why the
command was stopped.

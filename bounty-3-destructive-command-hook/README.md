# Destructive Command Guard Hook

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they
run. It reads the hook JSON payload from stdin, inspects Bash tool commands, logs
blocked attempts, and returns a clear denial message for Claude.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-guard.py ~/.claude/hooks/destructive-command-guard.py
chmod +x ~/.claude/hooks/destructive-command-guard.py
```

Add the hook to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- Recursive forced deletion: `rm -rf`, `rm -fr`, `rm --recursive --force`
- Destructive Git pushes: `git push --force`, `git push -f`
- SQL table destruction: `DROP TABLE`, `TRUNCATE`
- Broad SQL deletes: `DELETE FROM ...` without a `WHERE` clause

Normal commands pass through without logging or user interruption.

## Blocked Log

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes an ISO timestamp, project path, matching rule, and the
attempted command.

## Test

```bash
python -m unittest test_destructive_command_guard.py
```

The tests cover every required block pattern plus safe command pass-through.

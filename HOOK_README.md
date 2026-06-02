# Destructive Bash Guard Hook

PreToolUse hook for Claude Code that blocks destructive Bash commands before execution.

## Install

Run these two commands from the repository root:

```bash
python hooks/install_block_hook.py
python hooks/block_destructive_bash.py < hooks/sample-dangerous-input.json
```

The first command copies the hook to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`. The second command is a smoke test: it should print a JSON denial.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Normal Bash commands exit quietly with status `0`, so regular commands continue through Claude Code's normal permission flow.

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Claude Code Hook Format

The installer adds this PreToolUse configuration:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block_destructive_bash.py",
            "args": []
          }
        ]
      }
    ]
  }
}
```

When a blocked pattern is detected, the hook returns a `permissionDecision` of `deny` with a clear reason for Claude.

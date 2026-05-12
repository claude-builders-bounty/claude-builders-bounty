# Destructive Bash Command Blocker

This Claude Code `PreToolUse` hook blocks dangerous Bash commands before they run and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_blocker.py ~/.claude/hooks/
python3 ~/.claude/hooks/pre_tool_use_blocker.py --install
```

## What It Blocks

- `rm -rf` variants, including `rm -fr` and long options.
- `DROP TABLE`.
- `git push --force`, `git push -f`, and `git push --force-with-lease`.
- `TRUNCATE`.
- `DELETE FROM` without a `WHERE` clause.

Normal Bash commands pass through without output.

## Hook Format

The installer adds this hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_blocker.py"
          }
        ]
      }
    ]
  }
}
```

When a command is blocked, the hook returns a `permissionDecision: "deny"` response with a clear reason for Claude.

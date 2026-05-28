# Destructive Bash Command Guard

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

Run from this repository:

```bash
python3 hooks/install.py
```

The installer copies the hook to `~/.claude/hooks/pre_tool_use_guard.py` and registers it in `~/.claude/settings.json` for the `Bash` tool.

## What It Blocks

- `rm -rf` and equivalent `rm` invocations with recursive and force flags
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON with:

- timestamp
- attempted command
- project path
- block reason

Normal Bash commands exit without output so they do not interfere with Claude Code.

## Claude Code Hook Format

The installer writes this hook structure, using your absolute home path for the command:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/you/.claude/hooks/pre_tool_use_guard.py"
          }
        ]
      }
    ]
  }
}
```

When a command is blocked, the hook returns a `PreToolUse` deny decision with a clear reason for Claude.

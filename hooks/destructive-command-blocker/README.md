# Destructive Command Blocker Hook

Claude Code `pre-tool-use` hook that blocks dangerous Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-blocker/pre_tool_use.py ~/.claude/hooks/destructive-command-blocker.py && chmod +x ~/.claude/hooks/destructive-command-blocker.py
python ~/.claude/hooks/destructive-command-blocker.py --install
```

The installer writes this hook entry into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/destructive-command-blocker.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf` and flag variants such as `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `DELETE FROM` statements that do not include a `WHERE` clause

Safe commands pass through without output.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines:

```json
{"timestamp":"2026-05-29T12:00:00Z","command":"rm -rf build","project_path":"/repo","reason":"recursive force delete"}
```

## Manual Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' | python hooks/destructive-command-blocker/pre_tool_use.py
```

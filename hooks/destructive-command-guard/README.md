# Destructive Command Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py
python3 ~/.claude/hooks/destructive_command_guard.py --install
```

The installer adds this `PreToolUse` hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_command_guard.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf`, `rm -fr`, and equivalent recursive-force `rm` flag combinations
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `DELETE FROM ...` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- UTC timestamp
- attempted command
- project path from the hook payload
- block reason

## Behavior

The hook reads Claude Code hook JSON from stdin. It allows non-Bash tools and normal Bash commands with exit code `0`. When it detects a destructive command, it logs the attempt and returns a structured `PreToolUse` JSON response with `permissionDecision` set to `deny`, which blocks the tool call and shows the reason in Claude Code.

## Test

```bash
python3 destructive_command_guard.py --self-test
```

Sample blocked hook input:

```bash
printf '%s\n' '{"tool_name":"Bash","cwd":"/repo","tool_input":{"command":"rm -rf dist"}}' | python3 destructive_command_guard.py
```

Expected result: exit code `0`, a JSON deny response on stdout, and one JSON line in `~/.claude/hooks/blocked.log`.

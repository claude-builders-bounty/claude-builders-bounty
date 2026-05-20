# Destructive Command Guard

Pre-tool-use hook for Claude Code that blocks high-risk Bash and SQL commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-guard/destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py && chmod +x ~/.claude/hooks/destructive_command_guard.py
```

```bash
python3 hooks/destructive-command-guard/install.py
```

The installer adds this project-level hook entry to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PROJECT_DIR}/hooks/destructive-command-guard/destructive_command_guard.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- Recursive forced removal such as `rm -rf`, `rm -fr`, or `rm -r -f`
- Force pushes such as `git push --force`, `git push -f`, or `git push --force-with-lease`
- SQL table destruction through `DROP TABLE` or `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, command, reason, and project path.

## Manual Test

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}' | python3 hooks/destructive-command-guard/destructive_command_guard.py
```

Expected result: JSON with `permissionDecision` set to `deny`, and a new row in `~/.claude/hooks/blocked.log`.


# Destructive Command Guard Hook

Claude Code `PreToolUse` hook for Bash commands. It blocks obvious destructive
commands before they run, returns a Claude-readable denial reason, and appends
each blocked attempt to `~/.claude/hooks/blocked.log`.

## What It Blocks

- `rm` commands that combine recursive and force flags, including `rm -rf` and
  `rm -fr`
- `git push -f`, `git push --force`, and `git push --force-with-lease`
- SQL executed through common database clients that contains `DROP TABLE`,
  `TRUNCATE`, or `DELETE FROM` without a `WHERE` clause

Normal commands such as `git status`, `npm test`, `truncate -s 0 debug.log`,
and `DELETE FROM ... WHERE ...` statements are allowed.

## Install

Run one command from the repository root:

```bash
python3 hooks/destructive-command-guard/install.py
```

The installer copies the hook into `~/.claude/hooks/` and adds this Claude Code
configuration to `~/.claude/settings.json` without removing existing hooks:

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

## Manual Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/project"}' \
  | python3 hooks/destructive-command-guard/destructive_command_guard.py
```

Expected result: JSON with `permissionDecision` set to `deny`.

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git status --short"},"cwd":"/tmp/project"}' \
  | python3 hooks/destructive-command-guard/destructive_command_guard.py
```

Expected result: no output and exit code `0`.

## Run Tests

```bash
python3 -m unittest discover -s tests
```

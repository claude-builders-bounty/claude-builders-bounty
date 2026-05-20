# Bash Guard PreToolUse Hook

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

Bounty target: Claude Builders Bounty #3.

## Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- Project path
- Matched rule
- Attempted command

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp submissions/bash-guard-hook/bash_guard.py ~/.claude/hooks/bash_guard.py
chmod +x ~/.claude/hooks/bash_guard.py
```

Then add this hook to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Manual test

Allowed command:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/project"}' | python3 bash_guard.py
```

Blocked command:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf dist"},"cwd":"/tmp/project"}' | python3 bash_guard.py
```

The blocked command exits non-zero and writes to `~/.claude/hooks/blocked.log`.

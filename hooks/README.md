# Destructive Bash Command Blocker

This Claude Code `PreToolUse` hook blocks common destructive Bash commands before Claude can execute them.

It blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log row includes:

- UTC timestamp
- block reason
- project path
- attempted command

## Install

From the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add this matcher to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Manual Test

Allowed command:

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/project","tool_input":{"command":"npm test"}}' | python3 hooks/block_destructive_bash.py
```

Blocked command:

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/project","tool_input":{"command":"rm -rf dist"}}' | python3 hooks/block_destructive_bash.py
```

The blocked command exits with status `2`, writes the reason to `stderr`, and logs to `~/.claude/hooks/blocked.log`.


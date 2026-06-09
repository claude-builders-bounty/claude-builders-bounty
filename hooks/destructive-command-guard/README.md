# Destructive Command Guard Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before execution.

## Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` or `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with timestamp, reason, attempted command, and project path.

## Install

```bash
mkdir -p ~/.claude/hooks
cp destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py
```

Add this to your Claude Code settings file, for example `~/.claude/settings.json`:

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

## Test

```bash
python3 test_guard.py
```

## Example Block Message

```text
Blocked destructive Bash command: rm -rf. Review the command and request explicit human approval before retrying.
```

## Example Log Entry

```json
{"timestamp":"2026-06-09T09:52:00+00:00","reason":"rm -rf","command":"rm -rf build","project_path":"/path/to/project"}
```

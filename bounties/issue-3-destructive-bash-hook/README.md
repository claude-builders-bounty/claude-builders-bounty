# Destructive Bash Command Hook

Claude Code `PreToolUse` hook for issue #3. It blocks dangerous Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add this hook to `~/.claude/settings.json`:

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

## What It Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause
- `git push --force`, `git push -f`, and `git push --force-with-lease`

Safe commands exit normally with no output, so regular Bash usage is not interrupted.

## Log Format

Each blocked command is appended as one JSON line:

```json
{"timestamp":"2026-06-06T06:00:00+00:00","attempted_command":"rm -rf build","project_path":"/path/to/project","reason":"rm -rf / rm -fr"}
```

## Test

```bash
python -m unittest discover -s tests
```

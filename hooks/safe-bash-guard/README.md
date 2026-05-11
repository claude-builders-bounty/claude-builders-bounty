# Safe Bash Guard Hook

Claude Code `PreToolUse` hook that blocks destructive shell and SQL commands before the Bash tool runs.

## Install

From this repository:

```bash
bash hooks/safe-bash-guard/install.sh
```

Restart Claude Code after installing.

## What It Blocks

- `rm -rf` and equivalent recursive-force `rm` forms
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM ...` statements that do not include `WHERE`

Normal Bash commands continue without output or interruption.

## Hook Format

The installer adds this Claude Code hook entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/safe_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

The hook reads Claude Code's JSON event from stdin and returns a structured `permissionDecision: "deny"` only when a dangerous command is detected.

## Block Log

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- `timestamp`
- `project_path`
- `command`
- `reason`

Example:

```json
{"timestamp":"2026-05-11T15:30:00Z","project_path":"/repo","command":"rm -rf dist","reason":"recursive force deletion"}
```

## Run Tests

```bash
python3 -m unittest hooks/safe-bash-guard/test_safe_bash_guard.py
```

The tests cover blocked patterns, safe commands, and the `DELETE FROM` with `WHERE` exception.

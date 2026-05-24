# Destructive Bash Guard for Claude Code

A zero-dependency Claude Code `PreToolUse` hook that blocks destructive Bash
commands before they run.

## Install

From this repository:

```bash
chmod +x install.sh
./install.sh
```

The installer copies the hook to `~/.claude/hooks/destructive-bash-guard.py`,
marks it executable, and adds a `PreToolUse` hook entry for the `Bash` tool in
`~/.claude/settings.json`.

## What it blocks

- `rm -rf` style recursive forced removals
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `DELETE FROM ...` statements that do not include a `WHERE` clause

Normal commands such as `ls`, `npm test`, `git status`, `SELECT ...`, and
`DELETE FROM table WHERE id = 1` are allowed.

## Logging

Every blocked attempt is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- UTC timestamp
- attempted command
- project path
- block reason

Example:

```json
{"timestamp":"2026-05-24T00:00:00+00:00","project_path":"/repo","command":"rm -rf .","reason":"Blocked recursive forced removal: `rm -rf` can irreversibly delete project or system files."}
```

## Manual configuration

If you prefer to configure Claude Code manually, add this to
`~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/home/you/.claude/hooks/destructive-bash-guard.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

When a dangerous command is detected, the hook:

1. writes a JSONL entry to `~/.claude/hooks/blocked.log`,
2. prints a clear block decision and explanation for Claude, and
3. exits non-zero so the command is not executed.

If a blocked command is intentional, run it manually after human review.

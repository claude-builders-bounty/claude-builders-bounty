# Destructive Command Guard

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before
they run.

## Install

From this directory:

```bash
python3 install.py
```

Restart Claude Code after installing so it reloads `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and common flag variants like `rm -fr`, `rm -r -f`, and
  `rm --recursive --force`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` when the SQL statement has no `WHERE` clause
- `git push --force`, `git push -f`, force-with-lease variants, and forced
  refspec pushes like `git push origin +main`

Normal Bash commands exit with status `0` and no output, so Claude Code proceeds
normally.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log entry is JSON Lines and includes:

- `timestamp`
- `attempted_command`
- `project_path`
- `rules`

## Claude Code Format

The installer copies the hook to:

```text
~/.claude/hooks/destructive-command-guard.py
```

Then it adds this `PreToolUse` hook entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
```

When a command is blocked, the hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command..."
  }
}
```

## Test

From the repository root:

```bash
python3 -m unittest discover -s hooks/destructive-command-guard/tests
```

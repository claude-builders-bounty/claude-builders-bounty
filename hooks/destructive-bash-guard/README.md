# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

```bash
python3 hooks/destructive-bash-guard/install.py
python3 -m unittest discover -s hooks/destructive-bash-guard/tests
```

The installer copies the hook to `~/.claude/hooks/destructive_bash_guard.py`
and merges this Bash `PreToolUse` entry into `~/.claude/settings.json` without
removing existing hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

The hook reads the standard Claude Code hook JSON payload from stdin. It denies
commands that match any of these destructive patterns:

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` or `git push -f`
- `DELETE FROM ...` without a `WHERE` clause

Every denied command is appended to `~/.claude/hooks/blocked.log` with a
timestamp, attempted command, project path, and reason. Allowed commands exit
quietly and do not interfere with normal Bash usage.

## Test

```bash
python3 -m unittest discover -s hooks/destructive-bash-guard/tests
```

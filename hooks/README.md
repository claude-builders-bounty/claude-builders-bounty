# Destructive Bash Blocker Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

From this repository:

```bash
python3 hooks/install.py
```

The installer copies the hook to `~/.claude/hooks/block-destructive-bash.py` and registers it in `~/.claude/settings.json` with a `PreToolUse` matcher for the `Bash` tool.

## What It Blocks

- `rm -rf` and equivalent split flags such as `rm -r -f`
- `git push --force` and `git push -f`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended as JSON lines to `~/.claude/hooks/blocked.log` with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

Normal Bash commands exit cleanly without output, so Claude Code can continue without extra noise.

## Manual Settings

If you do not want to use the installer, add this to `~/.claude/settings.json` and adjust the path if needed:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/home/you/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

## Verify

```bash
python3 -m unittest discover -s tests
```

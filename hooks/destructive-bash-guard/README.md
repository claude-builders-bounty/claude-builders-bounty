# Destructive Bash Guard

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they run.

It blocks:

- `rm -rf` and equivalent recursive forced `rm` flags
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

## Install

Run this from the repository root:

```bash
python3 scripts/install_destructive_bash_hook.py
```

## Verify

Run a harmless command in Claude Code; it should proceed normally. Then ask Claude Code to run a destructive command such as `rm -rf tmp`. The hook exits with code `2`, blocks the command, and returns a clear explanation to Claude Code.

## Hook Format

The installer writes this Claude Code hook shape to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["~/.claude/hooks/block_destructive_bash.py"]
          }
        ]
      }
    ]
  }
}
```

The installed version uses the exact Python executable that ran the installer and the absolute hook path, so it also works on systems where `python3` is not on `PATH`.

# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

From this repository:

```bash
python .claude/hooks/install-block-destructive-bash.py
```

Restart Claude Code after installing.

## What It Blocks

- `rm -rf` and equivalent recursive forced `rm` flags
- `git push --force` and `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- reason

Normal commands such as `npm test`, `git status`, `rm file.txt`, and `DELETE FROM table WHERE id = 1` are allowed.

## Claude Code Settings

The installer writes this hook into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

The actual installer uses your current Python executable path so the command works in the active environment.

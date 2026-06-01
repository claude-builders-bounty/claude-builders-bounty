# Destructive Command Guard Hook

Claude Code `PreToolUse` hook for the `Bash` tool that blocks common destructive commands before they run.

## What it blocks

- `rm -rf` / `rm -fr` / equivalent recursive forced `rm` invocations
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push -f`
- `DELETE FROM` statements that do not contain a `WHERE` clause before the end of the SQL statement

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

Normal Bash commands exit successfully and are not logged.

## Install

From this repository, install in one command:

```bash
python3 install_destructive_command_guard.py
```

Restart Claude Code after installation.

The installer copies the hook to `~/.claude/hooks/destructive_command_guard.py` and adds this Claude Code hook configuration to `~/.claude/settings.json`:

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

## Manual install

If you prefer not to use the installer, copy `.claude/hooks/destructive_command_guard.py` into `~/.claude/hooks/`, make it executable, and add the JSON configuration above to your Claude Code settings.

## Local test

```bash
python3 tests/test_destructive_command_guard.py
```

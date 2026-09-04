# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

```bash
python bounties/003-destructive-bash-hook/install.py
```

The installer copies the hook to `~/.claude/hooks/destructive_bash_guard.py` and adds a `PreToolUse` Bash hook to `~/.claude/settings.json`. If settings already exist, the installer first writes `~/.claude/settings.json.bak`.
The saved hook command uses the same Python interpreter that ran the installer.

## What It Blocks

- `rm` with both recursive and force flags, including `rm -rf`, `rm -fr`, `rm -r -f`, and `rm --recursive --force`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL `DROP TABLE` sent to common SQL clients such as `psql`, `mysql`, `sqlite3`, `duckdb`, or entered as a direct SQL command
- SQL `TRUNCATE` sent to common SQL clients or entered as a direct SQL command
- SQL `DELETE FROM` statements without a `WHERE` clause when sent to common SQL clients or entered as direct SQL

Normal Bash commands exit silently with no hook output, so Claude Code continues as usual. Text-only mentions such as `echo "DROP TABLE users"` or `grep "DELETE FROM" migrations/*.sql` are allowed unless they are piped into a SQL client.

## Log File

Every blocked command appends one JSON line to:

```text
~/.claude/hooks/blocked.log
```

Each entry contains:

- UTC timestamp
- attempted command
- project path from the Claude Code hook input `cwd`
- block reason

## Manual Configuration

If you prefer to copy the hook yourself, add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/destructive_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Run Tests

```bash
python -m unittest discover -s bounties/003-destructive-bash-hook/tests
```

# Destructive Bash Command Blocker

Python Claude Code `PreToolUse` hook that blocks destructive Bash commands before they execute.

## Quick Install

```bash
./hooks/install.sh
python3 -m unittest discover -s tests
```

## Claude Code settings.json

Add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm` commands that combine recursive and force flags, including `rm -rf`, `rm -fr`, and `sudo rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause
- `git push --force`
- `git push -f`
- `git push --force-with-lease`

The hook only inspects Claude Code `Bash` tool calls. Other tool calls are ignored.

## What It Allows

- Quoted text such as `echo "rm -rf /"`
- Search commands such as `grep "DROP TABLE" file.sql`
- Scoped deletes such as `DELETE FROM users WHERE id = 1`
- Normal pushes such as `git push origin main`
- Non-forced removals such as `rm -r ./tmp` and `rm -f ./file.txt`

## Behavior

Claude Code sends hook JSON on stdin. Safe commands exit `0` without output. Blocked commands exit `2` and print a clear reason to stderr so Claude can choose a safer action.

Blocked attempts are appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- `timestamp`
- `command`
- `project_path`
- `reason`

## Test

```bash
python3 -m unittest discover -s tests
```

## Dependencies

No third-party dependencies are required. The hook uses only the Python standard library.

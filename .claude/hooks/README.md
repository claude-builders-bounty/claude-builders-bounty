# Destructive Bash Command Guard

This Claude Code `PreToolUse` hook blocks high-risk Bash commands before they run.
It is intended as a small safety rail for projects that use Claude Code with shell access.

## What It Blocks

- `rm -rf` style recursive forced deletion
- `DROP TABLE` SQL statements
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE` SQL statements
- `DELETE FROM ...` SQL statements that do not include a `WHERE` clause

Safe commands such as `ls`, `git status`, and `npm test` are allowed.

When a command is blocked, the hook exits with status code `2`, writes a clear reason to
stderr, and appends a JSON line to `~/.claude/hooks/blocked.log`.
Each log entry includes a timestamp, project path, reason, and attempted command.

## Install

Run this from the repository root:

```bash
python .claude/hooks/install_destructive_bash_hook.py
```

The installer copies the hook into `~/.claude/hooks/` and merges this configuration
into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Example

Claude Code sends hook input on stdin. For this payload:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "git push --force origin main"
  },
  "cwd": "/path/to/project"
}
```

The hook blocks the command and returns:

```text
Blocked destructive Bash command: force push. This command was not executed and was recorded in ~/.claude/hooks/blocked.log.
```

## Test

Run the test suite from this directory:

```bash
python -m unittest discover -s tests
```

# block-destructive-commands

A Claude Code `PreToolUse` hook that intercepts dangerous Bash commands
before they run.

## What it blocks

| Pattern | Examples |
|---------|----------|
| `rm` recursive + force | `rm -rf`, `rm -fr`, `rm -f -r`, `rm --recursive --force` |
| `git push` force | `git push --force`, `-f`, `--force-with-lease`, `--force-if-includes` |
| `DROP TABLE` | `psql -c "DROP TABLE users"` |
| `TRUNCATE` | `TRUNCATE t`, `TRUNCATE TABLE t` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` |

Commands are inspected per shell segment, so `cd / && rm -rf x`,
`cat f | rm -rf b`, and `VAR=1 rm -rf x` are all caught. `DELETE FROM`
is allowed when a `WHERE` clause is present. Everything else passes
through untouched, and the hook fails open if it ever receives
malformed input, so it can't break your session.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-commands.py -o ~/.claude/hooks/block-destructive-commands.py && chmod +x ~/.claude/hooks/block-destructive-commands.py
```

Then register it once in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/block-destructive-commands.py" }
        ]
      }
    ]
  }
}
```

## How it works

Claude Code pipes a JSON payload on stdin (`tool_name`, `tool_input.command`,
`cwd`, ...). The hook exits `0` to allow, or exits `2` to block — stderr
is shown to Claude as the reason, so the model can pick a safer approach.

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as
`timestamp <TAB> project path <TAB> command` for auditability.

# Claude Code Destructive Command Blocker

This is a Claude Code `PreToolUse` hook for `Bash` that blocks common destructive shell and SQL commands before they run.

## What It Blocks

- `rm -rf ...`
- `DROP TABLE ...`
- `TRUNCATE ...`
- `DELETE FROM ...` statements that do not include a `WHERE` clause
- `git push --force`, `git push --force-with-lease`, and `git push -f`

Normal commands such as `npm test`, `ls`, `git status`, and `DELETE FROM ... WHERE ...` pass through silently.

## Install

Run these two commands from this repository:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_commands.py
python3 scripts/install_settings.py
```

The installer merges the hook into `~/.claude/settings.json` under:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

A standalone settings example is also available at `examples/settings.json`.

## Behavior

When Claude Code is about to run a Bash command, this hook reads the hook payload from stdin. If the command is safe, it exits with no output and Claude Code continues normally.

If a destructive command is detected, the hook returns:

```json
{
  "decision": "block",
  "reason": "Blocked destructive command before execution. Reason: recursive force deletion with rm -rf. Ask the user for explicit confirmation and suggest a safer alternative."
}
```

## Audit Log

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- UTC timestamp
- attempted command
- project path
- block reasons

Example:

```json
{"timestamp":"2026-06-17T12:00:00+00:00","project_path":"/Users/me/app","command":"rm -rf node_modules","reasons":["recursive force deletion with rm -rf"]}
```

## Tests

```bash
python3 -m unittest discover -s tests
```


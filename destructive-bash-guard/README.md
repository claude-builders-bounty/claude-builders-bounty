# Destructive Bash Guard for Claude Code

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they execute.

It denies these patterns:

- `rm -rf` and equivalent recursive+force variants such as `rm -fr`, `rm -r -f`, and `rm --recursive --force`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes a UTC timestamp, attempted command, matched pattern, and project path.

## Install

From this directory, run these two commands:

```bash
mkdir -p ~/.claude/hooks && cp block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
python3 ~/.claude/hooks/block-destructive-bash.py --install
```

The second command idempotently merges this `PreToolUse` hook into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/you/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

When Claude Code attempts a dangerous Bash command, the hook returns a deny decision:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command (rm -rf): Recursive forced remove is destructive and must be reviewed by a human. Project: /path/to/project. Logged to /Users/you/.claude/hooks/blocked.log."
  }
}
```

Normal Bash commands exit with status `0` and no output, so they continue without interruption.

## Manual test

Allow case:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/tmp/project"}' | python3 block-destructive-bash.py
```

Blocked case:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' | python3 block-destructive-bash.py
```

## Design notes

- The hook only inspects `Bash` tool calls.
- Plain output commands such as `echo "DROP TABLE"` and `printf "DELETE FROM users"` are allowed to reduce documentation-related false positives.
- SQL passed to clients inside shell quotes is still inspected, so `psql -c 'DROP TABLE users'` is blocked.
- `DELETE FROM` is checked per SQL statement, so `DELETE FROM users; SELECT ... WHERE ...` is still blocked.
- The install command preserves existing settings and avoids duplicate hook entries.

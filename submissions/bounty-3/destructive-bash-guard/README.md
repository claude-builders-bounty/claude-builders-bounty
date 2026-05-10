# Destructive Bash Guard for Claude Code

This submission implements bounty #3: a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they execute.

## Install

From this directory:

```bash
chmod +x install.sh
./install.sh
```

The installer copies `destructive_bash_guard.py` to `~/.claude/hooks/` and registers this user-level hook in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

The hook blocks the required destructive patterns:

| Pattern | Example |
| --- | --- |
| `rm -rf` | `rm -rf build`, `sudo rm -fr /tmp/cache` |
| `DROP TABLE` | `sqlite3 app.db 'DROP TABLE users'` |
| `git push --force` | `git push origin main --force`, `git push -f origin main` |
| `TRUNCATE` | `psql -c 'TRUNCATE audit_log'` |
| `DELETE FROM` without `WHERE` | `sqlite3 app.db 'DELETE FROM sessions;'` |

It allows normal commands, including safe deletes without `-f`, normal `git push`, and SQL deletes with a `WHERE` clause.

## Claude Code Hook Behavior

The script follows the current Claude Code hook format:

- Reads hook input JSON from stdin.
- Only inspects `PreToolUse` events for the `Bash` tool.
- Allows unrelated tools and safe Bash commands without output.
- On a blocked command, writes a JSON response with:
  - `hookSpecificOutput.hookEventName = "PreToolUse"`
  - `hookSpecificOutput.permissionDecision = "deny"`
  - `hookSpecificOutput.permissionDecisionReason` explaining the block.

This avoids the deprecated `decision: "block"` PreToolUse format.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines:

```json
{"timestamp":"2026-05-10T12:00:00+00:00","project_path":"/repo","reason":"rm with recursive and force flags can delete large directory trees","command":"rm -rf dist"}
```

Each entry includes the required timestamp, attempted command, and project path.

## Test

```bash
python3 -m unittest test_destructive_bash_guard.py
```

The tests verify all required block patterns, safe commands, the current Claude Code denial schema, and log creation. They do not execute any destructive command.

# Claude Code Safety Hook — Block Destructive Bash Commands

A `pre-tool-use` hook for Claude Code that intercepts dangerous shell commands
before they execute, logs every blocked attempt, and explains to Claude why the
command was refused.

## Install (2 commands)

```bash
cp hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Then add the hook to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py" }]
      }
    ]
  }
}
```

## What it blocks

| Category | Examples |
|----------|----------|
| Filesystem | `rm -rf`, `rm -r -f`, `rm --no-preserve-root`, `dd of=/dev/sda` |
| Database | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| Git | `git push --force`, `git push -f`, `git push -F` |
| System | `chmod 777 /…`, fork bomb `:(){ :|:& };:` |

**Warns but does not block:** `git push --force-with-lease` (logged with level WARN)

**Specifically allowed:**
- `rm -r` without `-f` (non-forced recursive remove)
- `DELETE FROM … WHERE …` (safe targeted deletes)
- `git push --force-with-lease` (safer force variant)

## Logs

Every blocked (and warned) attempt is appended to `~/.claude/hooks/blocked.log`
as a JSON line:

```json
{"timestamp": "2026-05-12T10:00:00+00:00", "level": "BLOCK", "command": "rm -rf /", "details": "rm -rf — recursive forced removal...", "project_path": "/home/user/myproject"}
```

## Tests

```bash
cd bounties/003-destructive-bash-hook
python3 -m pytest tests/ -v     # requires: pip install pytest
```

26 tests covering: safe pass-through, all blocked categories, DELETE with/without
WHERE (including multi-line SQL), split flags (`rm -r -f`), force-with-lease
warn-only, malformed input, and non-Bash tool calls.

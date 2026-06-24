# Claude Destructive Command Guard

PreToolUse hook for Claude Code that blocks destructive Bash and SQL commands before they run.

## Install

```bash
python3 install.py
```

Manual configuration is also available in `settings.example.json`.

## What It Blocks

- `rm -rf` and equivalent recursive forced deletion variants
- `git push --force`, `git push -f`, `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended as JSONL to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and reason.

## Example

Input:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf dist"
  },
  "cwd": "/repo"
}
```

Output:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive shell command: recursive forced deletion via rm."
  }
}
```

## Validation

Run:

```bash
python3 -m unittest test_pre_tool_use_guard.py
```

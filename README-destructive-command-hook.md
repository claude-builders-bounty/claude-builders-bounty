# Destructive Command PreToolUse Hook

Python `PreToolUse` hook for Claude Code that blocks destructive Bash commands before they run.

## Blocks

- `rm -rf`, including combined or reordered `-r`/`-f` flags
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements that do not include `WHERE`

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- `timestamp`
- `attempted_command`
- `project_path`

Normal Bash commands exit silently and are allowed.

## Install

```bash
python3 install_destructive_command_hook.py
```

## Test

```bash
python3 tests/test_block_destructive_commands.py
```

## Example Hook Output

When a blocked command is attempted, the hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked rm command with both recursive and force flags. Command was logged to ~/.claude/hooks/blocked.log."
  }
}
```

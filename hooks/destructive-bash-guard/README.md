# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-bash-guard/pre_tool_use.py ~/.claude/hooks/destructive-bash-guard.py && chmod +x ~/.claude/hooks/destructive-bash-guard.py
```

```bash
~/.claude/hooks/destructive-bash-guard.py --install
```

## What It Blocks

- `rm -rf` and equivalent recursive-force delete forms
- `DROP TABLE` and `DROP DATABASE`
- `git push --force`, `git push -f`, and force-with-lease variants
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are logged to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, attempted command, project path, matched rule, and reason.

## Test

```bash
python hooks/destructive-bash-guard/test_pre_tool_use.py
```

To preview the settings entry without writing files:

```bash
python hooks/destructive-bash-guard/pre_tool_use.py --print-settings
```

The hook follows the current Claude Code `PreToolUse` JSON output shape:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "..."
  }
}
```

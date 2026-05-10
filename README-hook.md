# Claude Code destructive Bash blocker hook

This is a Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-dangerous-bash.py ~/.claude/hooks/block-dangerous-bash.py
python3 ~/.claude/hooks/block-dangerous-bash.py --help >/dev/null 2>&1 || true
```

Add this hook entry to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-dangerous-bash.py"
          }
        ]
      }
    ]
  }
}
```

## What it blocks

The hook denies Bash tool calls matching these destructive patterns:

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Every blocked attempt is appended as JSONL to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- UTC timestamp
- attempted command
- project path
- matched rule

Normal Bash commands exit with code `0` and no output, so they are not affected.

## Example denial output

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked dangerous Bash command (rm -rf): Recursive forced deletion can destroy project or system files."
  }
}
```

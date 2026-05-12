# Claude Code Safety Hook

A `pre-tool-use` hook for Claude Code that blocks destructive bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

Add this matcher to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use.sh"
          }
        ]
      }
    ]
  }
}
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` without a `WHERE` clause

## What it logs

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each line contains:

- timestamp
- project path
- attempted command

## Hook behavior

- returns a Claude Code `permissionDecision: deny` response for blocked commands
- prints a clear explanation for Claude Code in `permissionDecisionReason`
- lets normal bash commands pass through untouched

## Quick test

```bash
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | ./pre-tool-use.sh
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"echo safe"}}' | ./pre-tool-use.sh
```

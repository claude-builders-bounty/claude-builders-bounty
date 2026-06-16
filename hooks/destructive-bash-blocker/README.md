# Claude Code Destructive Bash Guard

Solution starter for Claude Builders Bounty issue:

`[BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands`

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

## What It Blocks

This Claude Code `PreToolUse` hook blocks dangerous Bash commands before execution:

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to:

`~/.claude/hooks/blocked.log`

Each log line includes:

- timestamp
- project path
- attempted command
- matching rule
- reason

## Install

From this folder:

```bash
python install.py
```

That command copies the hook into `~/.claude/hooks/` and merges the `PreToolUse` hook into `~/.claude/settings.json`.

## Manual Configuration

If you prefer to install manually, copy `block_destructive.py` into `~/.claude/hooks/` and add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["~/.claude/hooks/block_destructive.py"]
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python -m unittest discover -s tests
```

## Claude Code Hook Behavior

The hook reads the event JSON from stdin. For Bash tool calls, it inspects `tool_input.command`.

Allowed commands exit `0` with no output.

Blocked commands print this JSON shape:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: ..."
  }
}
```

This follows the current Claude Code hooks reference for `PreToolUse` decision control.

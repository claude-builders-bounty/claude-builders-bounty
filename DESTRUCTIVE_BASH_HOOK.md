# Destructive Bash Command Blocker for Claude Code

A Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## What it blocks

The hook denies Bash commands containing:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes a timestamp, the attempted command, and the project path.

## Install

From this repository root:

```bash
chmod +x install.sh && ./install.sh
```

Restart Claude Code after installing so it reloads `~/.claude/settings.json`.

## Claude Code hook configuration

The installer adds this `PreToolUse` hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

Claude Code sends hook input as JSON on stdin. When the hook detects a destructive command, it returns a `permissionDecision: "deny"` response with a clear reason for Claude.

## Example blocked response

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: rm -rf. Command was not executed."
  }
}
```

Normal Bash commands exit cleanly with no output, so they do not interfere with Claude Code's regular workflow.

## Test

```bash
python3 -m unittest discover -v
```

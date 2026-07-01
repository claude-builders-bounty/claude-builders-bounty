# Block Destructive Bash Commands

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they run.

It is designed for `~/.claude/hooks/` and only matches the Bash tool.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- timestamp
- attempted command
- project path
- matched block reason

## Install

Run this from the repository root:

```bash
python3 hooks/block-destructive-bash/install.py
```

Restart Claude Code after installing.

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and updates `~/.claude/settings.json` with this hook entry:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

For safe Bash commands, the hook exits without a decision and normal Claude Code permission flow continues.

For blocked commands, the hook returns a Claude Code `PreToolUse` deny decision with a clear reason. The Bash tool call does not run.

Example blocked response:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: matched rm -rf. The command was not run. Use a safer, scoped command or ask the user for explicit approval before destructive operations."
  }
}
```

## Test

```bash
python3 hooks/block-destructive-bash/test_block_destructive_bash.py
```

The test suite verifies destructive patterns are blocked and normal commands like `git push origin main`, `rm -r tmp`, `truncate -s 0 app.log`, and `npm test` are allowed.

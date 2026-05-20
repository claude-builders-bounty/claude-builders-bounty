# Destructive Bash Command Guard

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## What It Blocks

- `rm -rf` variants, including `rm -fr`, `rm -r -f`, and `sudo rm -rf`
- SQL `DROP TABLE`
- SQL `TRUNCATE` / `TRUNCATE TABLE`
- `git push --force` and `git push -f`
- `DELETE FROM` statements that do not contain a `WHERE` clause

Allowed commands produce no output and continue normally. Blocked commands are denied with Claude Code's `hookSpecificOutput.permissionDecision = "deny"` response and are logged to `~/.claude/hooks/blocked.log`.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-guard/block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 hooks/destructive-command-guard/install.py
```

The installer merges this hook into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/you/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 hooks/destructive-command-guard/test_block_destructive_bash.py
```

Manual blocked-command check:

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}' | python3 hooks/destructive-command-guard/block_destructive_bash.py
```

Expected behavior: the hook emits a JSON deny decision and appends one JSON-line record to `~/.claude/hooks/blocked.log` with timestamp, attempted command, reason, and project path.

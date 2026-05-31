# Destructive Bash Command Blocker

This Claude Code `PreToolUse` hook blocks high-risk Bash commands before they run.

It blocks:

- `rm -rf` and equivalent recursive force `rm` flags
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause
- `git push --force`, `git push --force-with-lease`, and `git push -f`

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, project path, and block reason.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python hooks/install_settings.py
```

The installer adds this hook to `~/.claude/settings.json` while preserving existing settings.

## Manual Settings

If you prefer to edit settings yourself, add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python -m unittest tests/test_block_destructive_bash.py
```

You can also smoke-test the hook directly:

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/project","tool_input":{"command":"rm -rf build"}}' | python hooks/block_destructive_bash.py
```

The hook exits with `0` and returns a Claude Code `permissionDecision: "deny"` JSON response for blocked commands. Safe commands produce no output and exit with `0`.

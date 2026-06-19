# Destructive Command Hook

This Claude Code `PreToolUse` hook blocks high-risk Bash commands before they run and records every blocked attempt in `~/.claude/hooks/blocked.log`.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook/pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py && chmod +x ~/.claude/hooks/pre_tool_use_blocker.py
python destructive-command-hook/install_settings.py
```

The installer adds this hook to `~/.claude/settings.json` under the `PreToolUse` event with matcher `Bash`.

## What It Blocks

- `rm -rf` and equivalent combined `rm` flags containing both recursive and force
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause
- `git push --force`, `git push -f`, and `git push --force-with-lease`

Normal Bash commands exit with status `0` and continue through the usual Claude Code permission flow. Blocked commands exit with status `2` and send a clear reason to Claude on stderr.

## Hook Input

Claude Code sends `PreToolUse` JSON on stdin. For Bash, the hook reads:

```json
{
  "cwd": "/path/to/project",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  }
}
```

## Local Verification

```bash
python destructive-command-hook/test_hook.py
```


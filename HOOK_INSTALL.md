# Destructive Command Hook

Claude Code pre-tool-use hook that blocks destructive bash commands and logs blocked attempts to `~/.claude/hooks/blocked.log`.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook.py ~/.claude/hooks/destructive-command-hook.py && chmod +x ~/.claude/hooks/destructive-command-hook.py
```

## Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/project"}' | ~/.claude/hooks/destructive-command-hook.py
```

Add it to `~/.claude/settings.json` as a `PreToolUse` command hook with matcher `Bash`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/destructive-command-hook.py" }
        ]
      }
    ]
  }
}
```

The hook exits non-zero, prints a clear block reason, and appends a JSON line with timestamp, attempted command, and project path to `~/.claude/hooks/blocked.log`.

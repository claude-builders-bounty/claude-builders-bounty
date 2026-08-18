# Block destructive bash (Claude Code PreToolUse hook)

Intercepts Bash tool calls and denies `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`/`-f`, and `DELETE FROM` with no WHERE. Allowed commands are untouched.

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as: UTC timestamp, project path, reason, command.

## Install (2 commands)

From this folder:

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
```

Then merge this into `~/.claude/settings.json` (create the file if missing):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

On Windows use `python` instead of `python3` if that is the interpreter on PATH.

The hook exits 0 and prints `hookSpecificOutput.permissionDecision = deny` on stdout so Claude Code treats it as a deny, not a crash.

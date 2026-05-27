# Claude PreToolUse Bash Blocker

This is a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

Blocked patterns: `rm -rf`; `git push --force`, `git push -f`, and forced `+ref` pushes; `DROP TABLE`; `TRUNCATE`; and `DELETE FROM` statements that do not include a `WHERE` clause.

Blocked attempts are written to `~/.claude/hooks/blocked.log` as JSON lines with a timestamp, attempted command, project path, rule, and reason.

## Install

From this repository root:

```bash
mkdir -p ~/.claude/hooks && cp block-dangerous-bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-dangerous-bash.py
python3 ~/.claude/hooks/block-dangerous-bash.py --install-user-settings
```

The installer adds this Claude Code hook configuration to `~/.claude/settings.json`:

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

## Behavior

When a dangerous command is detected, the hook exits with code `2` and writes a clear explanation to stderr, which Claude Code feeds back to Claude. Normal Bash commands exit with code `0` and do not produce output.

Example blocked log entry:

```json
{"timestamp":"2026-05-27T05:00:00+00:00","project_path":"/work/project","rule":"rm-rf","reason":"recursive forced removal with rm is blocked","command":"rm -rf dist"}
```

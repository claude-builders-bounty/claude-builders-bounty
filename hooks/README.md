# Destructive Bash Blocker Hook

Claude Code `PreToolUse` hook for Bash commands. It blocks high-risk commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Blocks

- `rm -rf` and `rm -fr` style recursive force deletion.
- `DROP TABLE`.
- `git push --force` and `git push -f`.
- `TRUNCATE`.
- `DELETE FROM` without a `WHERE` clause.

Normal Bash commands pass through without output or interference.

## Install

```bash
python3 hooks/block_destructive.py --install
python3 ~/.claude/hooks/block_destructive.py --self-test
```

## Hook Configuration

The installer copies the hook into `~/.claude/hooks/block_destructive.py` and appends this Claude Code hook entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

The exact Python path in the generated settings file uses the interpreter that ran `--install`.

## Blocked Log Format

Each blocked attempt is appended as one JSON line:

```json
{"timestamp":"2026-06-16T00:00:00+00:00","attempted_command":"rm -rf build","project_path":"/path/to/project","reason":"`rm -rf` style recursive force deletion"}
```

The hook exits with code `2` for blocked commands and writes a clear explanation for Claude Code.

# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

From this repository:

```bash
python hooks/install_block_destructive_bash.py
```

Restart Claude Code or run `/hooks` to confirm the `PreToolUse` matcher for `Bash` is registered.

## What It Blocks

- `rm -rf`, `rm -fr`, `rm -r -f`, and equivalent recursive forced deletion flags
- `DROP TABLE`
- `git push -f`, `git push --force`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not contain a `WHERE` clause

Normal Bash commands exit successfully and are not logged.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON and includes:

- timestamp
- attempted command
- project path

## Claude Code Hook Format

The installer adds this entry to `~/.claude/settings.json`:

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

When a dangerous command is detected, the hook prints a clear explanation to
Claude Code using `hookSpecificOutput.permissionDecision: "deny"`, which blocks
the tool call and gives Claude the reason.

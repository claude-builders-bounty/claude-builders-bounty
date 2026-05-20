# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that denies high-risk Bash commands before they run.

## Install

```bash
python3 hooks/destructive-command-blocker/install.py
```

Restart Claude Code after installation.

## What It Blocks

- `rm -rf` / `rm -fr`, including nested `bash -c` calls
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Blocked attempts are written as JSON lines to:

```text
~/.claude/hooks/blocked.log
```

Each entry includes the UTC timestamp, attempted command, block reason, and project path.

## Claude Code Settings

The installer adds this hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["~/.claude/hooks/block_destructive_bash.py"]
          }
        ]
      }
    ]
  }
}
```

The actual generated config uses the current Python executable path so paths with spaces work safely.

## Test

```bash
python3 -m unittest discover hooks/destructive-command-blocker/tests
```

Safe commands exit silently and allow Claude Code to continue. Blocked commands return a Claude Code-compatible `permissionDecision: "deny"` JSON response explaining why the command was stopped.

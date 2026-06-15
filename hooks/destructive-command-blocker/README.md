# Destructive Command Blocker Hook

Blocks risky Bash commands before Claude Code can run them.

## Install

```bash
python hooks/destructive-command-blocker/install.py
```

## What It Blocks

- `rm -rf` and equivalent recursive-force `rm` flag combinations
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with a timestamp,
the attempted command, and the project path from the Claude Code hook payload.

## How It Works

The installer copies `block_destructive_bash.py` into `~/.claude/hooks/` and
adds this Claude Code hook configuration to `~/.claude/settings.json`:

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

For safe commands, the hook exits silently and does not change Claude Code's
normal permission flow. For blocked commands, it returns a `PreToolUse` deny
decision with a clear reason for Claude.

## Verify

```bash
python hooks/destructive-command-blocker/test_block_destructive_bash.py
```


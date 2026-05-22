# Destructive Command Blocker for Claude Code

Claude Code `PreToolUse` hook for Bash commands. It blocks destructive command patterns before they run, writes each blocked attempt to `~/.claude/hooks/blocked.log`, and otherwise stays silent so normal Bash commands continue through Claude Code's regular permission flow.

## Install

From this repository:

```bash
python3 hooks/destructive-command-blocker/install.py
```

The installer copies `block_destructive_commands.py` into `~/.claude/hooks/` and adds this `PreToolUse` hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/python",
            "args": ["/home/you/.claude/hooks/block_destructive_commands.py"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf`, including `rm -fr`, `sudo rm -Rf`, and long-form `rm --recursive --force`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause
- `git push --force`, `git push -f`, and `git push --force-with-lease`

`--force-with-lease` is intentionally blocked. It is safer than `--force`, but it still rewrites a remote branch, so the hook requires an explicit manual override instead of allowing it by default.

Safe examples such as `npm test`, `git push origin main`, and `DELETE FROM users WHERE id = 42` return no output and do not interfere with Claude Code.

## Blocked Log Format

Each blocked attempt is appended as JSON Lines:

```json
{"attempted_command":"rm -rf build","project_path":"/repo","reason":"rm with both recursive and force flags is blocked","timestamp":"2026-05-22T11:00:00Z"}
```

Set `CLAUDE_BLOCKED_LOG=/custom/path.log` before launching Claude Code to write the log somewhere else.

## Test

```bash
python3 hooks/destructive-command-blocker/test_block_destructive_commands.py
```

The tests execute the hook as Claude Code would: JSON on stdin, denial JSON on stdout for blocked commands, and empty stdout for safe commands.

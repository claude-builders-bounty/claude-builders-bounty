# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

From a cloned copy of this repository:

```bash
python3 hooks/install_destructive_bash_guard.py
```

Or from scratch:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python3 claude-builders-bounty/hooks/install_destructive_bash_guard.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and updates `~/.claude/settings.json`.

## What It Blocks

- `rm -rf`, including combined or reordered flags such as `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Safe Bash commands continue through the normal Claude Code permission flow.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log entry is one JSON line with:

- UTC timestamp
- attempted command
- project path
- block reason
- tool name and tool use id when provided by Claude Code

## Manual Settings Entry

If you prefer to copy the file yourself, add this to `~/.claude/settings.json` and replace the script path with your local copy:

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
            "args": ["/absolute/path/to/block_destructive_bash.py"]
          }
        ]
      }
    ]
  }
}
```

The hook returns Claude Code's current `hookSpecificOutput.permissionDecision` format with `permissionDecision: "deny"` for blocked commands.

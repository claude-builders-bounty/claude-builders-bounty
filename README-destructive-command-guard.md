# Destructive Command Guard Hook

Claude Code `PreToolUse` hook for blocking destructive Bash commands before they run.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python claude-builders-bounty/install.py
```

The installer copies `hooks/destructive-command-guard.py` to `~/.claude/hooks/` and adds a `PreToolUse` matcher for the `Bash` tool to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent recursive forced deletion forms such as `rm -fr`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL destructive statements when sent through a database CLI or migration tool:
  - `DROP TABLE`
  - `TRUNCATE`
  - `DELETE FROM` without a `WHERE` clause

Allowed commands produce no stdout and exit `0`, so Claude Code continues through the normal permission flow.

## Blocked Attempt Log

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Manual Configuration

If you prefer not to use the installer, copy the hook to `~/.claude/hooks/destructive-command-guard.py` and add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python \"~/.claude/hooks/destructive-command-guard.py\""
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python -m pytest
```

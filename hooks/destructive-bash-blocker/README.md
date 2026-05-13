# Destructive Bash Blocker

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-bash-blocker/block_destructive_bash.py ~/.claude/hooks/
python3 hooks/destructive-bash-blocker/install.py
```

The installer updates `~/.claude/settings.json` with a `PreToolUse` hook for the `Bash` tool.

## What It Blocks

- `rm -rf` style recursive force deletes, including `rm -fr`, `rm -r -f`, and long-option variants
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- `timestamp`
- `command`
- `project_path`
- `reason`

Safe commands exit cleanly without stdout so Claude Code's normal permission flow remains unchanged.

## Manual Settings

If you prefer to edit settings yourself, add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 hooks/destructive-bash-blocker/tests/test_block_destructive_bash.py
```

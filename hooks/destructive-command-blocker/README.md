# Destructive Command Blocker Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## What It Blocks

- `rm -rf` and equivalent clustered options such as `rm -fr`
- `git push --force` and `git push --force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp, the attempted command, the project path, and the rule that blocked it.

## Install

```sh
cd hooks/destructive-command-blocker
./install.sh
```

The installer copies `block_destructive_command.py` into `~/.claude/hooks/`, detects `python3` or `python`, and merges the hook configuration into `~/.claude/settings.json`.

## Manual Configuration

If you prefer to configure it yourself, copy `block_destructive_command.py` to `~/.claude/hooks/` and add this to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_command.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```sh
python3 test_block_destructive_command.py
```

Use `python` instead of `python3` if that is the executable name on your system.

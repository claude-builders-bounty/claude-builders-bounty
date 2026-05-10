# Safe Bash PreToolUse Hook

Block destructive Bash commands before Claude Code runs them.

## Install

```bash
bash safe-bash-hook/install.sh
```

```bash
python3 ~/.claude/hooks/block_destructive_bash.py < safe-bash-hook/examples/safe-command.json
```

## Claude Code Settings

The installer writes this hook entry to `~/.claude/settings.json`:

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

## Behavior

The hook blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Test

```bash
python3 safe-bash-hook/test_hook.py
```

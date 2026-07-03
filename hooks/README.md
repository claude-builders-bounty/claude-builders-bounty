# Destructive Bash Blocker — Claude Code Hook

Blocks dangerous bash commands before execution. Bounty submission.

## Install (1 command + paste settings)

```bash
bash hooks/install.sh
```

Copy `hooks/settings.sample.json` into `~/.claude/settings.json` (merge with existing keys).

Or manual install:

```bash
mkdir -p ~/.claude/hooks
cp block_destructive.py ~/.claude/hooks/block_destructive.py
```

Add to `~/.claude/settings.json` (or use `hooks/settings.sample.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python ~/.claude/hooks/block_destructive.py" }]
      }
    ]
  }
}
```

## Test

```bash
bash hooks/run_tests.sh
# or: python hooks/test_hook.py
```

- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, reason, project path, and command.

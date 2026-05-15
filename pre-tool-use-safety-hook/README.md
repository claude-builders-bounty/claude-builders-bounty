# Pre-Tool-Use Safety Hook

Blocks destructive Bash commands before Claude Code can run them.

## Install

```bash
cd pre-tool-use-safety-hook
bash install.sh
```

The installer copies the hook to `~/.claude/hooks/block-destructive-bash.py` and registers it in `~/.claude/settings.json` as a `PreToolUse` hook for the `Bash` tool.

## What Gets Blocked

- `rm -rf` and equivalent combined recursive/force flags such as `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, attempted command, project path, and block reason.

## Hook Format

The hook uses the Claude Code `PreToolUse` JSON contract:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

Safe Bash commands exit normally. Blocked commands return a `permissionDecision: deny` response with a clear reason so Claude can choose a safer command or ask the user for explicit approval.

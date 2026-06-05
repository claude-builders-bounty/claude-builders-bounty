# Claude Code PreToolUse Safety Hook

This bounty implementation adds a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## What it blocks

- `rm -rf` variants, including `rm -fr` and `sudo rm -rf`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- `DELETE FROM` SQL statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, project path, reason, and attempted command.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use-safety-hook/pre_tool_use_safety.py ~/.claude/hooks/pre_tool_use_safety.py
chmod +x ~/.claude/hooks/pre_tool_use_safety.py
```

Add this hook entry to your Claude Code settings file:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre_tool_use_safety.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python pre-tool-use-safety-hook/test_pre_tool_use_safety.py
```

The tests verify every blocked pattern from the bounty acceptance criteria and confirm normal Bash commands continue without hook output.

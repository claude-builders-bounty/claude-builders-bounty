# Destructive-command PreToolUse Hook

This Claude Code `PreToolUse` hook blocks a small, explicit set of dangerous
Bash commands before they run:

- recursive forced removal (`rm -r`/`-R` with `-f`/`--force`);
- forced `git push`;
- `DROP TABLE` and `TRUNCATE`;
- `DELETE FROM` statements without a `WHERE` clause.

Blocked attempts are written as JSON Lines to `~/.claude/hooks/blocked.log`.
Malformed or unrelated hook events are allowed through so the hook does not
break other Claude Code tools.

## Install

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/
```

Add this command to the `PreToolUse` / `Bash` hook entry in your Claude Code
settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_commands.py"}
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 tests/test_hook.py
```

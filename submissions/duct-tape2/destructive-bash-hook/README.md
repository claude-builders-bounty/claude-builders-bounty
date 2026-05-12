# Destructive Bash PreToolUse Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
python3 scripts/install-settings.py
```

## What it blocks

- `rm` with both recursive and force flags, including `rm -rf`, `rm -fr`, and split flags like `rm -r -f`.
- `git push --force`, `git push -f`, and `git push --force-with-lease`.
- SQL `DROP TABLE`.
- SQL `TRUNCATE` / `TRUNCATE TABLE`.
- SQL `DELETE FROM` statements that do not include a `WHERE` clause.

## What it allows

- Normal Bash commands such as `ls`, `npm test`, `git push`, `rm file.txt`, and `DELETE FROM ... WHERE ...`.
- Passive text inspection such as `echo "DROP TABLE users"` or `grep "DELETE FROM" migration.sql`.
- Non-Bash Claude Code tool calls.

## Hook behavior

The hook reads Claude Code's JSON hook payload from stdin. When the tool is `Bash` and the command matches a blocked pattern, it:

1. Appends a JSON line to `~/.claude/hooks/blocked.log`.
2. Includes timestamp, attempted command, project path, matched rule, and reason.
3. Returns a Claude Code `hookSpecificOutput` response with `permissionDecision: "deny"`.

Safe commands exit with status 0 and no stdout, so they do not interfere with normal Bash usage.

## Example settings

The installer writes this shape into `~/.claude/settings.json` without removing existing hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/you/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

## Run tests

```bash
python3 -m unittest tests/test_block_destructive_bash.py
```

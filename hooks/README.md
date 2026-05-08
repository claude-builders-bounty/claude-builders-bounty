# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before execution.

It blocks:

- `rm -rf` and equivalent recursive-force `rm` flag combinations
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push -f`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/
python ~/.claude/hooks/block_destructive_bash.py --install
```

The installer registers this hook in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Manual Test

Allowed command:

```bash
python hooks/block_destructive_bash.py --check-command "git status"
```

Blocked command:

```bash
python hooks/block_destructive_bash.py --check-command "DELETE FROM users"
```

## Hook Behavior

The hook reads Claude Code hook JSON from `stdin`. It only evaluates `PreToolUse` events for the `Bash` tool, so normal non-Bash tools are not affected.

When a command is blocked, the hook returns a `PreToolUse` `permissionDecision: "deny"` response with a clear reason for Claude and writes the blocked attempt to `~/.claude/hooks/blocked.log`.


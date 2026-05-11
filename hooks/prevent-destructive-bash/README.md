# Destructive Bash Guard for Claude Code

This PreToolUse hook blocks high-risk Bash commands before Claude Code runs
them. It is intentionally narrow: it only inspects `Bash` tool calls and lets
normal commands continue.

## What It Blocks

- `rm -rf` style recursive force deletion, including `rm -fr`, `rm -r -f`,
  `rm --recursive --force`, and case variants
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL statements containing `DROP TABLE`
- SQL statements containing `TRUNCATE`
- `DELETE FROM ...` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- project path
- blocked reason
- attempted command

## Install

Run from the repository root:

```bash
python hooks/prevent-destructive-bash/install.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py`
and adds this matcher to `~/.claude/settings.json`:

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
printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git status"},"cwd":"/tmp/demo"}' | python hooks/prevent-destructive-bash/block_destructive_bash.py
```

Blocked command:

```bash
printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/demo"}' | python hooks/prevent-destructive-bash/block_destructive_bash.py
```

## Development

Run the tests:

```bash
python -m unittest hooks/prevent-destructive-bash/test_block_destructive_bash.py
```

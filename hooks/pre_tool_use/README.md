# Block destructive bash commands

This `PreToolUse` hook blocks obviously destructive Bash commands before Claude Code runs them.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON with:

- `timestamp`
- `command`
- `project_path`

## Install

```bash
./hooks/pre_tool_use/install.sh
```

That single command:

1. copies the hook to `~/.claude/hooks/block_destructive_commands.py`
2. registers it in `~/.claude/settings.json` for `PreToolUse` on the `Bash` matcher

## Quick verification

```bash
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./tmp"},"cwd":"/tmp/demo"}' | ~/.claude/hooks/block_destructive_commands.py
```

You should get a JSON response with `"permissionDecision":"deny"`.

## Notes

- Safe commands such as `git status` pass through silently.
- The hook is intentionally conservative: if a command matches one of the destructive patterns above, it is denied and logged.

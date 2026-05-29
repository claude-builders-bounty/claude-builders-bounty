# PreToolUse Guard Hook (Claude Code)

Blocks common destructive `Bash` commands before Claude Code runs them, and logs every blocked attempt to:

- `~/.claude/hooks/blocked.log` (timestamp, project path, reason, command)

## What it blocks

- `rm -rf` / `rm -fr`
- `git push --force` / `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` (when no `WHERE` is present)

## Install (2 commands)

1) Clone this repo:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty && cd claude-builders-bounty
```

2) Run the installer:

```bash
./tools/pre_tool_use_guard/install.sh
```

That’s it — it updates `~/.claude/settings.json` to register the hook.


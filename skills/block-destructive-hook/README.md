# 🛡️ Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

A safety hook that prevents Claude Code from running destructive bash commands that could cause data loss.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/block-destructive-hook/hook.sh -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it! The hook is active for all Claude Code sessions.

## What It Blocks

- `rm -rf /` or `rm -rf ~` (recursive force delete)
- `DROP TABLE`, `TRUNCATE TABLE`, `DROP DATABASE` (SQL destruction)
- `git push --force`, `git push -f` (remote history overwrite)
- `DELETE FROM` without `WHERE` clause (full table wipe)
- `mkfs`, `dd` to block devices (disk formatting)
- `shred -zuz` (secure deletion)
- `truncate --size=0` (file emptying)

## Override

To run a blocked command, use Claude Code's per-command approval:

```
--confirm
```

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-02 10:30:15] TOOL=bash PROJECT=/home/user REASON=DROP TABLE... COMMAND=DROP TABLE users;
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## Requirements

- Bash 4.0+
- curl (for installation)
- Claude Code

## License

MIT

# Claude Safe Hook

A pre-tool-use hook for Claude Code that blocks destructive bash commands.

## Features

- Blocks dangerous commands: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- Logs all blocked attempts to `~/.claude/hooks/blocked.log`
- Clear feedback messages for Claude

## Installation (2 commands)

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy hook script
curl -o ~/.claude/hooks/pre_tool_use_hook.py https://raw.githubusercontent.com/ZG361/claude-safe-hook/main/pre_tool_use_hook.py && chmod +x ~/.claude/hooks/pre_tool_use_hook.py
```

## Usage

Once installed, the hook automatically intercepts all bash/exec commands. No manual activation needed.

### Example Blocked Commands

```bash
rm -rf /important/data        # BLOCKED
DROP TABLE users;             # BLOCKED
git push --force origin main  # BLOCKED
TRUNCATE logs;                # BLOCKED
DELETE FROM users;            # BLOCKED (no WHERE)
```

### Example Allowed Commands

```bash
rm single_file.txt            # OK (not recursive)
DELETE FROM users WHERE id=1  # OK (has WHERE)
git push origin main          # OK (no force)
```

## Log Format

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-09T10:15:30.123456] BLOCKED: 'rm -rf /data' - Reason: rm -rf: recursive/force delete - Path: /home/user/project
```

## Requirements

- Python 3.6+
- Claude Code CLI

## Bounty

This hook was created for the [$100 Bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) on claude-builders-bounty.

## License

MIT

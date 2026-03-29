# Claude Code Security Hook

A pre-tool-use hook that intercepts and blocks dangerous bash commands before they are executed by Claude Code.

## 💰 Bounty

This hook was created for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) - $100 reward.

## Features

- ✅ **Blocks dangerous commands**: rm -rf /, DROP TABLE, git push --force, etc.
- ✅ **Logs all blocked attempts**: Timestamp, command, project path, severity
- ✅ **Smart pattern matching**: Regex-based detection with severity levels
- ✅ **Safe pattern overrides**: Allows --dry-run and --force-with-lease
- ✅ **Fail-open design**: Hook errors don't block legitimate commands
- ✅ **Clear user feedback**: Explains why command was blocked

## Installation (< 2 commands)

```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/claude-security-hook/main/install.sh | bash

# Or manual installation
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Blocked Commands

| Pattern | Example | Severity |
|---------|---------|----------|
| rm -rf / | `rm -rf /` | CRITICAL |
| DROP TABLE | `DROP TABLE users` | CRITICAL |
| DROP DATABASE | `DROP DATABASE production` | CRITICAL |
| TRUNCATE | `TRUNCATE TABLE logs` | HIGH |
| DELETE without WHERE | `DELETE FROM users` | HIGH |
| git push --force | `git push --force origin main` | MEDIUM |
| Database overwrite | `> /path/to/db.sqlite` | HIGH |
| Disk formatting | `mkfs.ext4 /dev/sda1` | CRITICAL |
| Direct disk write | `dd if=/dev/zero of=/dev/sda` | CRITICAL |

## Safe Overrides

These patterns are allowed even if they match blocked patterns:

- `--dry-run` flag: `rm -rf /tmp/test --dry-run`
- `--force-with-lease`: `git push --force-with-lease`

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-29T09:15:30.123456]
  SEVERITY: CRITICAL
  PATTERN: Destructive deletion (rm -rf /)
  COMMAND: rm -rf /important/data
  PROJECT: /home/user/myproject
  ACTION: BLOCKED
============================================================
```

## Testing

Run the test suite:

```bash
python3 test-hook.py
```

## How It Works

1. Claude Code reads hooks from `~/.claude/hooks/`
2. Before executing any bash tool, Claude calls `pre-tool-use.py`
3. The hook checks the command against blocked patterns
4. If blocked: logs the attempt, prints warning, exits with code 1
5. If safe: exits with code 0, Claude proceeds with execution

## Hook API

This hook implements the [Claude Code hooks API](https://docs.anthropic.com/claude-code/hooks):

- **Type**: `pre-tool-use`
- **Input**: JSON with `command` and `working_directory`
- **Output**: Exit code 0 (allow) or 1 (block)
- **Side effects**: Writes to `~/.claude/hooks/blocked.log`

## License

MIT License - Feel free to modify and distribute.

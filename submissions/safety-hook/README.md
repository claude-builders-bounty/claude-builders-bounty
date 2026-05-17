<<<<<<< HEAD
# 🛡️ Claude Code Safety Hook

A pre-tool-use hook for Claude Code that blocks destructive bash commands before they are executed.

## Features

- 🚫 Blocks dangerous commands: `rm -rf`, `DROP TABLE`, `git push --force`, etc.
- 📝 Logs all blocked attempts with timestamp, command, and project path
- 💬 Displays clear warning messages to Claude
- 🔒 Does not interfere with normal bash commands
- ⚡ Fast and lightweight Python script

## Blocked Patterns

| Pattern | Severity | Description |
|---------|----------|-------------|
| `rm -rf /` | CRITICAL | Deleting root directory |
| `rm -rf ~` | CRITICAL | Deleting home directory |
| `rm -rf .` | CRITICAL | Deleting current directory |
| `DROP TABLE` | HIGH | Dropping database tables |
| `git push --force` | HIGH | Force pushing to git |
| `TRUNCATE TABLE` | HIGH | Truncating tables |
| `DELETE FROM` (no WHERE) | HIGH | Unconditional delete |
| `> /system/file` | MEDIUM | Overwriting system files |
| `mkfs.*` | CRITICAL | Formatting filesystems |
| `dd if=* of=/dev/*` | CRITICAL | Writing to devices |
| Fork bomb | CRITICAL | Resource exhaustion attack |

## Installation (2 Commands)

```bash
# 1. Clone and enter directory
git clone https://github.com/1150654748m-dev/claude-safety-hook.git && cd claude-safety-hook

# 2. Install hook
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

When Claude Code attempts to execute a bash command:

1. The hook intercepts the command
2. Checks against dangerous patterns
3. If dangerous: blocks execution and logs attempt
4. If safe: allows execution normally

## Log File

Blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Log format:
```
[2026-03-28T18:30:00.000000] SEVERITY: CRITICAL | PATTERN: rm -rf / | COMMAND: rm -rf / | PATH: /home/user/project
=======
# Claude Safety Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they are executed.

## 💰 Bounty

This project was created for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) - $100 reward.

## Features

- ✅ Blocks destructive patterns:
  - `rm -rf` on root, home, or wildcard paths
  - `DROP TABLE`, `TRUNCATE TABLE` SQL commands
  - `DELETE FROM` without WHERE clause
  - `git push --force` / `git push -f`
  - `git reset --hard`
  - Fork bombs (`:(){ :|:& };:`)
  - `dd` to system disks
  - `mkfs` on devices
  - Direct writes to disk devices

- ✅ Logs every blocked attempt to `~/.claude/hooks/blocked.log`
- ✅ Clear error messages explaining why commands were blocked
- ✅ Non-intrusive - only intercepts bash commands

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp safety_hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Or use the install script:

```bash
bash install.sh
>>>>>>> 7470341 (feat: add pre-tool-use hook to block destructive bash commands)
```

## Testing

<<<<<<< HEAD
Try these commands in Claude Code (they will be blocked):

```bash
# This will be blocked
rm -rf /

# This will be blocked
git push --force

# This will be blocked
DROP TABLE users;
=======
Test the hook with dangerous commands (they will be blocked):

```bash
# These will be blocked:
rm -rf /
rm -rf ~
rm -rf *
git push --force
git reset --hard
DROP TABLE users;
DELETE FROM users;
```

Check the log:

```bash
cat ~/.claude/hooks/blocked.log
```

## Log Format

```
[2026-05-17T13:45:30.123456] BLOCKED: rm -rf on root or system directories
  Command: rm -rf /
  Project: /home/user/myproject
------------------------------------------------------------
>>>>>>> 7470341 (feat: add pre-tool-use hook to block destructive bash commands)
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## License

MIT

# Claude Code Pre-Tool-Use Hook: Destructive Command Blocker

A safety hook for Claude Code that intercepts and blocks dangerous bash commands before they execute.

## Features

- ✅ Blocks `rm -rf` and recursive deletes
- ✅ Blocks database destruction (`DROP TABLE`, `TRUNCATE`, `DELETE FROM` without WHERE)
- ✅ Blocks force git pushes (`git push --force`)
- ✅ Blocks system-level dangerous commands (fork bombs, disk formatting)
- ✅ Logs all blocked attempts with timestamps
- ✅ Clear explanations when commands are blocked
- ✅ Zero interference with safe commands

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/install.sh | bash
```

Or manually:

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use-blocker.py > ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

When Claude Code attempts to execute a bash command, this hook:

1. Intercepts the command before execution
2. Checks against known dangerous patterns
3. If dangerous: blocks execution, logs the attempt, and explains why
4. If safe: allows execution to proceed normally

## Blocked Commands

| Pattern | Example | Reason |
|---------|---------|--------|
| `rm -rf` | `rm -rf /` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users` | Database table deletion |
| `TRUNCATE` | `TRUNCATE TABLE orders` | Table data deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Unconditional data deletion |
| `git push --force` | `git push origin main --force` | Force push overwrites history |
| Fork bomb | `:(){ :|:& };:` | System crash |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Disk formatting |
| `dd` to device | `dd if=/dev/zero of=/dev/sda` | Direct disk write |

## Log File

Blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Example log entry:
```
[2026-04-02T12:34:56.789012] BLOCKED: rm -rf: Recursive force delete
  Command: rm -rf /important/data
  Project: /home/user/my-project
--------------------------------------------------
```

## Testing

Test the hook with a safe command:
```bash
echo "This will work normally"
```

Test the hook with a blocked command:
```bash
rm -rf /tmp/test-directory
# Hook will block this and show explanation
```

## Uninstallation

```bash
rm ~/.claude/hooks/pre-tool-use
```

## Requirements

- Python 3.6+
- Claude Code with hooks support

## License

MIT

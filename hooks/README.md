# Claude Code Security Hook

A `pre-tool-use` hook that blocks destructive bash commands before they execute.

## 🚀 Quick Install (2 commands)

```bash
# 1. Copy hook to Claude Code hooks directory
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

Done! The hook is now active.

## 🛡️ What It Blocks

| Pattern | Example | Why Blocked |
|---------|---------|-------------|
| `rm -rf /` | `rm -rf /home/user/project` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | Database table deletion |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Table data deletion |
| `DELETE` (no WHERE) | `DELETE FROM users;` | Unconditional data loss |
| `git push --force` | `git push --force origin main` | Destructive git operation |
| `mkfs.*` | `mkfs.ext4 /dev/sda1` | Filesystem formatting |
| `dd to device` | `dd if=file of=/dev/sda` | Direct disk writes |
| Fork bombs | `:(){ :|:& };:` | Resource exhaustion attacks |

## 📋 Features

- ✅ Blocks dangerous commands before execution
- ✅ Logs all blocked attempts with timestamp, command, and project path
- ✅ Shows clear error message to Claude
- ✅ Does not interfere with normal bash commands
- ✅ Zero configuration required

## 📁 Log Location

Blocked commands are logged to:
```
~/.claude/hooks/blocked.log
```

Example log entry:
```
[2026-04-15T11:45:30.123456] BLOCKED: rm -rf: Recursive force delete detected
  Command: rm -rf /home/user/old-project
  Project: /home/user/current-project
------------------------------------------------------------
```

## 🔧 Testing

Test the hook:
```bash
# This should be blocked
echo '{"tool": "bash", "command": "rm -rf /tmp/test", "project_path": "/home/user"}' | ~/.claude/hooks/pre-tool-use

# This should pass
echo '{"tool": "bash", "command": "ls -la", "project_path": "/home/user"}' | ~/.claude/hooks/pre-tool-use
```

## ⚠️ Disclaimer

This hook provides an additional safety layer but is not a substitute for:
- Regular backups
- Careful code review
- Testing in safe environments

Always verify critical operations before execution.

## 💰 Bounty

This hook was created for [claude-builders-bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)
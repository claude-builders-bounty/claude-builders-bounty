# Claude Code Security Hook: Block Destructive Commands

A `pre-tool-use` hook for Claude Code that intercepts dangerous bash commands before execution.

## 🚀 Installation (2 commands or fewer)

```bash
# 1. Copy the hook to Claude Code hooks directory
mkdir -p ~/.claude/hooks && cp pre-tool-use-block-destructive.py ~/.claude/hooks/

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py
```

That's it! The hook will automatically activate on your next Claude Code session.

## 🔒 What It Blocks

### File System Destruction
- `rm -rf` (recursive force delete)
- `rm * -rf` (any rm with -rf flag)
- `:> file` (file truncation)
- `dd if=/dev/...` (disk destruction)

### Database Destruction
- `DROP TABLE` (table deletion)
- `TRUNCATE TABLE` (table truncation)
- `DELETE FROM table` (without WHERE clause)

### Git Destruction
- `git push --force` or `git push -f` (force push)
- `git reset --hard` (hard reset)

### System Commands
- `mkfs.*` (filesystem format)
- `fdisk /dev/...` (partition manipulation)
- `chmod 777` (insecure permissions)

### Shell Destruction
- Fork bombs `:(){ :|:& };:`
- `mv * /` (move to root)
- `> /dev/sd*` (write to disk devices)

## 📊 Logging

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Block reason
- Project path

Example log entry:
```json
{
  "timestamp": "2026-03-27T08:15:30.123456",
  "command": "rm -rf /home/user/project",
  "reason": "rm -rf (recursive force delete)",
  "project_path": "/home/user/project",
  "hook": "pre-tool-use-block-destructive"
}
```

## 🎯 How It Works

1. Claude Code sends tool use requests to the hook via stdin
2. Hook checks if it's an `exec` command with a bash command
3. If command matches dangerous patterns, it's blocked with explanation
4. Safe commands are allowed through
5. All blocked attempts are logged

## 🧪 Testing

Test the hook with:

```bash
# These will be blocked:
echo "Testing rm -rf"  # Simulated in test
echo "Testing DROP TABLE users"  # Simulated in test

# These will pass:
echo "ls -la"
echo "git status"
echo "SELECT * FROM users WHERE id = 1"
```

## 🛠️ Development

The hook is written in Python 3 and follows Claude Code's hook interface:

```python
# Input: JSON via stdin with tool request
# Output: JSON via stdout with {'allow': True/False, 'message': '...'}
```

## 📝 Requirements

- Python 3.6+
- Claude Code with hooks support
- Unix-like system (Linux, macOS, WSL)

## 🤝 Contributing

Found a dangerous pattern missing? Open an issue or PR!

## 📄 License

MIT License - see LICENSE file

## 💰 Bounty

This hook was created for the [$100 bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) on Opire.dev.
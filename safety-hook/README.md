# 🛡️ Claude Code Safety Hook

Pre-tool-use hook that blocks dangerous bash commands before they execute.

## 🚀 Installation

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the hook and make it executable
cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

# Done. Restart Claude Code to activate.
```

## 🎯 What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Irreversible file deletion |
| `DROP TABLE` | Database table destruction |
| `TRUNCATE` | Mass data loss |
| `git push --force` | Force overwrite remote history |
| `DELETE FROM` without `WHERE` | Delete all rows unintentionally |

## 📋 How It Works

- Passes through **all non-bash tools** (file reads, edits, web requests, etc.)
- Checks every bash command against dangerous patterns
- On block: logs the attempt + shows a clear message to Claude
- Safe commands like `ls`, `cat`, `git status`, `npm install` work normally

## 📁 Blocked Commands Log

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2026-05-16 12:00:00] BLOCKED: rm -rf /var/log | Cmd: rm -rf /var/log/* | Path: /home/user/project
```

## 🧪 Test It

```bash
# This should be BLOCKED:
echo "rm -rf /tmp/test"

# This should PASS:
echo "ls -la"
```

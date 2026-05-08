# Destructive Command Blocker Hook

Pre-tool-use Claude Code hook that blocks dangerous bash commands.

## Installation (2 Commands)

```bash
# 1. Download hook to Claude hooks directory
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/hook.py https://raw.githubusercontent.com/.../hook.py && chmod +x ~/.claude/hooks/hook.py

# 2. Add to settings.json
cat >> ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "pre-tool-use": [{"matcher": "bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/hook.py"}]}]
  }
}
EOF
```

## What It Blocks

| Command | Reason |
|---------|--------|
| `rm -rf /` | Root filesystem deletion |
| `rm -rf *` | All files in current directory |
| `rm -rf ~` | Home directory deletion |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE TABLE` | SQL data wipe |
| `DELETE FROM` (no WHERE) | Unconditional row deletion |
| `git push --force` | Force push (history rewrite) |
| `mkfs.*` | Filesystem format |
| `dd if=/dev/zero` | Disk wipe |

## Log File

Blocked attempts logged to: `~/.claude/hooks/blocked.log`

Format: `2026-05-08T20:12:00 command="rm -rf /" path="/home/user/project"`
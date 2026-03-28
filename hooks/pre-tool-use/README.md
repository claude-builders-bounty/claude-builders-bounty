# Block Destructive Commands Hook

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## 🛡️ Protected Patterns

This hook blocks the following destructive operations:

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete can destroy entire directory trees |
| `DROP TABLE` | Permanently deletes database tables |
| `git push --force` | Force push can overwrite remote history |
| `TRUNCATE` | Removes all rows without logging individual row deletions |
| `DELETE FROM` without WHERE | Deletes all rows from a table |

## 📦 Installation

**2 commands:**

```bash
# 1. Create hooks directory and download the hook
mkdir -p ~/.claude/hooks/pre-tool-use && curl -fsSL https://raw.githubusercontent.com/HuiNeng6/claude-builders-bounty/main/hooks/pre-tool-use/block-destructive-commands.py -o ~/.claude/hooks/pre-tool-use/block-destructive-commands.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use/block-destructive-commands.py
```

### Alternative (Windows PowerShell)

```powershell
# 1. Create hooks directory and download the hook
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\hooks\pre-tool-use" | Out-Null; Invoke-WebRequest -Uri "https://raw.githubusercontent.com/HuiNeng6/claude-builders-bounty/main/hooks/pre-tool-use/block-destructive-commands.py" -OutFile "$env:USERPROFILE\.claude\hooks\pre-tool-use\block-destructive-commands.py"

# 2. No chmod needed on Windows - the script will run with Python
```

## 📝 Logging

All blocked commands are logged to:

```
~/.claude/hooks/blocked.log
```

Log entries include:
- Timestamp
- Pattern name detected
- Description of the danger
- Project path
- Full attempted command

## 🔧 How It Works

1. Claude Code calls this hook before executing bash/exec commands
2. The hook checks the command against dangerous patterns
3. If a match is found:
   - The command is blocked
   - An explanatory message is shown to Claude
   - The attempt is logged
4. If no match, the command proceeds normally

## ⚙️ Configuration

The hook works out of the box. To customize:

1. Edit `~/.claude/hooks/pre-tool-use/block-destructive-commands.py`
2. Modify `DANGEROUS_PATTERNS` list to add/remove patterns
3. Each pattern has:
   - `pattern`: Regex pattern to match
   - `name`: Human-readable name
   - `description`: Why it's dangerous

## 🧪 Testing

Test that the hook is working:

```bash
# This should be blocked
echo "Test: rm -rf /some/directory"
```

Ask Claude to run `rm -rf /tmp/test` and it should be blocked with an explanation.

## 📄 License

MIT License - See [LICENSE](../../LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or PR at:
https://github.com/HuiNeng6/claude-builders-bounty
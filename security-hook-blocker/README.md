# Security Hook: Destructive Command Blocker

Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## What It Blocks

### File Operations
- `rm -rf` (recursive force delete)
- `rm -fr` (any variant with -r and -f flags)

### Database Operations
- `DROP TABLE`
- `DROP DATABASE`
- `TRUNCATE TABLE`
- `DELETE FROM [table]` without a WHERE clause

### Git Force Operations
- `git push --force`
- `git push -f`

### System-Level Operations
- Write operations to disk devices (`/dev/sd*`)
- `dd` to disk devices
- `chmod 777` (insecure permissions)
- `sudo rm -rf /`

## Installation

### Quick Install (2 commands)
```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/security-hook-blocker/pre-tool-use
chmod +x pre-tool-use && mkdir -p ~/.claude/hooks && mv pre-tool-use ~/.claude/hooks/
```

### Manual Install
```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the hook
cp pre-tool-use ~/.claude/hooks/

# 3. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

1. **Intercepts tool calls:** Runs before any bash/exec command
2. **Pattern matching:** Checks command against known dangerous patterns
3. **Blocks execution:** Prevents the command from running if dangerous
4. **Logs attempts:** Records blocked commands to `~/.claude/hooks/blocked.log`
5. **Informs Claude:** Returns a clear error message explaining why

## Usage

Once installed, the hook runs automatically. No configuration needed.

### Example: Blocked Command

**You ask Claude:**
> "Delete all files in this directory"

**Claude tries:**
```bash
rm -rf *
```

**Hook blocks it and returns:**
```
🚫 Security Hook: Command Blocked

The following command was blocked for safety:

rm -rf *

Reason: rm -rf (recursive force delete)

What happened:
- This command matches a known destructive pattern
- The attempt was logged to: ~/.claude/hooks/blocked.log
- Project path: /home/user/my-project

What to do:
- If this is intentional, review the command carefully
- Consider using safer alternatives
- For file deletion, use specific paths instead of wildcards
```

## Viewing Blocked Commands

```bash
# View all blocked attempts
cat ~/.claude/hooks/blocked.log

# View recent blocks (last 10)
tail -n 10 ~/.claude/hooks/blocked.log

# Pretty-print JSON log
jq '.' ~/.claude/hooks/blocked.log
```

### Log Format

Each blocked command is logged as JSON:
```json
{
  "timestamp": "2026-03-29T15:45:30.123456",
  "tool": "bash",
  "command": "rm -rf /important/data",
  "reason": "rm -rf (recursive force delete)",
  "project_path": "/home/user/my-project"
}
```

## Overriding the Hook

If you need to run a blocked command intentionally:

### Option 1: Run in terminal directly
```bash
# The hook doesn't affect your terminal
rm -rf ./build
```

### Option 2: Temporarily disable
```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled
# Run your command via Claude
mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use
```

### Option 3: Modify the hook
Edit `~/.claude/hooks/pre-tool-use` and comment out specific patterns.

## Testing

### Test 1: Block rm -rf
```bash
# Install the hook first, then ask Claude:
# "Delete all temporary files recursively"
# Expected: Blocked with clear error message
```

### Test 2: Block DROP TABLE
```bash
# Ask Claude: "Drop the users table from the database"
# Expected: Blocked with SQL deletion warning
```

### Test 3: Block git push --force
```bash
# Ask Claude: "Force push this branch to origin"
# Expected: Blocked with git force operation warning
```

### Test 4: Allow safe commands
```bash
# Ask Claude: "Show me all files in this directory"
# Expected: Allowed (ls -la runs normally)
```

## Requirements

- Python 3.6+
- Claude Code with hooks support
- Unix-like system (Linux, macOS)

## Customization

Edit `pre-tool-use` and modify the `DANGEROUS_PATTERNS` list:

```python
DANGEROUS_PATTERNS = [
    (r'your_pattern_here', 'Description shown to user'),
    # Add more patterns as needed
]
```

Patterns use Python regular expressions (case-insensitive by default).

## Security Note

This hook is a **safety net**, not a security boundary. It:
- ✅ Prevents accidental destructive commands
- ✅ Logs suspicious activity
- ✅ Gives you time to review dangerous operations

It does **NOT**:
- ❌ Replace proper file permissions
- ❌ Prevent all possible destructive commands
- ❌ Protect against intentional malicious actions

Always review what Claude is doing, especially with sensitive operations.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
rm ~/.claude/hooks/blocked.log  # Optional: remove logs
```

## License

MIT — use freely, modify as needed.

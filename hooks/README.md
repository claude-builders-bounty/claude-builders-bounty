# Pre-Tool-Use Hook - Destructive Command Blocker

## Overview

This hook intercepts dangerous bash commands before they are executed by Claude Code, providing a safety layer against accidental data loss or system damage.

## Features

- **Always Blocked**: Critically dangerous commands (e.g., `rm -rf /`)
- **Requires Confirmation**: Risky commands that need explicit approval (e.g., `rm -rf ./folder`, `git push --force`)
- **Automatic Logging**: All blocked attempts are logged with timestamps
- **Pattern-Based Detection**: Regex patterns catch variations of dangerous commands

## Installation

### Step 1: Copy Hook File

```bash
# Create hooks directory if it doesn't exist
mkdir -p ~/.claude/hooks

# Copy the hook
cp blocked_commands_hook.py ~/.claude/hooks/blocked_commands_hook.py

# Make executable
chmod +x ~/.claude/hooks/blocked_commands_hook.py
```

### Step 2: Configure hooks.json

Create or edit `~/.claude/hooks.json`:

```json
{
  "hooks": [
    {
      "name": "blocked_commands_hook",
      "event": "pre-tool-use",
      "command": "python3 ~/.claude/hooks/blocked_commands_hook.py"
    }
  ]
}
```

### Step 3: Verify Installation

```bash
# Test the hook manually
python3 ~/.claude/hooks/blocked_commands_hook.py --test

# Check log file location
ls -la ~/.claude/hooks/blocked.log
```

## Blocked Commands

### Always Blocked (No Override)

| Command | Reason |
|---------|--------|
| `rm -rf /` | Deletes root filesystem |
| `rm -r -f /` | Deletes root filesystem (split flags) |
| `rm -rf /*` | Deletes all files |
| `rm -rf ~` | Deletes home directory |
| `sudo rm -rf /` | Root-level filesystem delete |
| `rm --no-preserve-root` | Bypasses rm safety check |
| `dd of=/dev/*` | Overwrites disk |
| `:(){ :|:& };:` | Fork bomb |
| `mkfs.*` | Formats disk |
| `chmod 777 /` | Dangerous permissions |
| `chown * /` | Changes root ownership |
| `sudo chmod 777` | Root-level dangerous permissions |
| `docker run -v /:/host` | Container escape |
| `mount --bind /` | Mount namespace escape |

### Requires Confirmation

| Command | Reason |
|---------|--------|
| `rm -rf *` | Recursive delete |
| `rm -rf ./folder` | Recursive delete (relative path) |
| `git push --force` | Rewrites history |
| `git push -f` | Rewrites history (short form) |
| `git reset --hard HEAD` | Discards all changes |
| `git clean -fdx` | Removes untracked files |
| `DROP TABLE *` | Deletes database table |
| `TRUNCATE *` | Empties table |
| `DELETE FROM *` | Deletes rows |
| `ALTER TABLE DROP COLUMN` | Removes column |
| `sudo rm *` | Root-level delete |
| `sudo su` | Switch to root |
| `sudo -i` | Root shell |
| `curl * | bash` | Remote code execution |
| `curl * | sudo` | Remote code execution as root |
| `wget * | bash` | Remote code execution |
| `export PATH=` | Modifies system path |
| `unset PATH` | Breaks command resolution |

## Usage Examples

### Example 1: Blocked Command

When Claude tries to run:
```bash
rm -rf /tmp/important-data
```

Hook response:
```json
{
  "allowed": false,
  "message": "🚫 Blocked dangerous command: REQUIRES_CONFIRMATION: Matches risky pattern '^rm\\s+(-[rf]+\\s+)?'",
  "blocked_command": "rm -rf /tmp/important-data",
  "reason": "REQUIRES_CONFIRMATION: Matches risky pattern '^rm\\s+(-[rf]+\\s+)?'",
  "suggestion": "This command could cause data loss or system damage. Please review and use a safer alternative, or add an explicit override flag.",
  "log_file": "/home/user/.claude/hooks/blocked.log"
}
```

### Example 2: Allowed Command

When Claude tries to run:
```bash
git commit -m "fix: bug"
```

Hook response:
```json
{
  "allowed": true
}
```

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-21T20:15:32.123456] BLOCKED: rm -rf /tmp/data | Reason: REQUIRES_CONFIRMATION: Matches risky pattern '^rm\s+(-[rf]+\s+)?'
[2026-04-21T20:16:45.789012] BLOCKED: DROP TABLE users | Reason: REQUIRES_CONFIRMATION: Matches risky pattern '^DROP\s+TABLE\s+'
```

## Customization

### Add Custom Patterns

Edit the hook file and add patterns to:

```python
# Always blocked (no override)
ALWAYS_BLOCKED_PATTERNS = [
    r'^your_pattern_here',
]

# Requires confirmation
REQUIRE_CONFIRMATION_PATTERNS = [
    r'^your_risky_pattern_here',
]
```

### Change Log Location

```python
LOG_FILE = Path('/custom/path/blocked.log')
```

## Testing

### Run Built-in Tests

```bash
python3 blocked_commands_hook.py --test
```

### Test with Sample Input

```bash
echo '{"tool": "bash", "command": "rm -rf /"}' | python3 blocked_commands_hook.py
```

Expected output:
```json
{
  "allowed": false,
  "message": "🚫 Blocked dangerous command: ...",
  ...
}
```

## Troubleshooting

### Hook Not Triggering

1. Check `~/.claude/hooks.json` syntax
2. Verify hook file is executable: `chmod +x ~/.claude/hooks/blocked_commands_hook.py`
3. Restart Claude Code

### False Positives

If a safe command is blocked:
1. Check which pattern matched
2. Refine the regex pattern
3. Add exception logic if needed

### Performance Issues

The hook runs synchronously before each bash command. If it's too slow:
1. Reduce the number of patterns
2. Optimize regex patterns
3. Consider compiling patterns at module load

## Security Notes

⚠️ **Important**: This hook is a safety net, not a replacement for careful code review. Always review commands before execution.

⚠️ **Bypass Warning**: Determined attackers can bypass this hook. Use it as one layer in a defense-in-depth strategy.

## License

MIT License - See repository LICENSE

## Bounty Information

This hook resolves **Issue #3** ($100 Bounty) from claude-builders-bounty.

**Acceptance Criteria Met:**
- ✅ Pre-tool-use hook in Python
- ✅ Blocks destructive commands (rm -rf, DROP TABLE, git push --force, etc.)
- ✅ Logs blocked attempts to ~/.claude/hooks/blocked.log
- ✅ Easy installation and configuration

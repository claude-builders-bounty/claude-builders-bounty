# Claude Code Security Hook

A pre-tool-use hook that blocks dangerous bash commands before they are executed by Claude Code.

## Features

✅ **Blocks dangerous commands:**
- `rm -rf` - Recursive force deletion
- `DROP TABLE` - SQL table deletion
- `TRUNCATE` - SQL table truncation
- `DELETE FROM` without WHERE - Unbounded deletion
- `git push --force` - Force push to remote
- `DROP DATABASE` - Database deletion

✅ **Logging:**
- All blocked attempts logged to `~/.claude/hooks/blocked.log`
- Includes timestamp, attempted command, project path

✅ **Clear feedback:**
- Explains why command was blocked
- Shows matched pattern and severity
- Indicates log file location

## Installation

### Method 1: Manual Installation

```bash
# Step 1: Create hooks directory
mkdir -p ~/.claude/hooks

# Step 2: Copy the hook
cp pre_tool_use.py ~/.claude/hooks/

# Step 3: Make executable
chmod +x ~/.claude/hooks/pre_tool_use.py
```

### Method 2: One-liner

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre_tool_use.py https://raw.githubusercontent.com/YOUR_FORK/claude-builders-bounty/main/solutions/issue-3/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

## How It Works

1. Claude Code invokes this hook before executing any bash command
2. Hook checks command against dangerous patterns
3. If safe → command is allowed
4. If dangerous → command is blocked and logged

## Testing

Test with a dangerous command (should be blocked):

```bash
# Test rm -rf
claude-code "Delete all files in /tmp with rm -rf"

# Test DROP TABLE
claude-code "Run SQL: DROP TABLE users;"

# Test git push --force
claude-code "Force push to origin with git push --force"
```

Check the log:

```bash
cat ~/.claude/hooks/blocked.log
```

## Example Output

When a dangerous command is blocked:

```
⚠️  BLOCKED: Dangerous command detected!

Command: rm -rf /home/user/project

Violations:
  ❌ rm -rf: Recursive force deletion can cause irreversible data loss
     Matched: 'rm -rf'
     Severity: HIGH

This attempt has been logged to: /home/user/.claude/hooks/blocked.log
```

## Log Format

Each blocked attempt is logged as JSON:

```json
{
  "timestamp": "2026-03-27T13:45:00.123456",
  "command": "rm -rf /home/user/project",
  "project_path": "/home/user/current-project",
  "violations": [
    {
      "name": "rm -rf",
      "pattern": "\\brm\\s+(-[rf]+\\s+|--recursive\\s+|--force\\s+)+",
      "reason": "Recursive force deletion can cause irreversible data loss",
      "severity": "HIGH",
      "matched_text": "rm -rf"
    }
  ]
}
```

## Configuration

To add custom dangerous patterns, edit the `DANGEROUS_PATTERNS` dictionary in `pre_tool_use.py`:

```python
DANGEROUS_PATTERNS = {
    "your-pattern-name": {
        "pattern": r"\bYOUR_REGEX_PATTERN\b",
        "reason": "Why this is dangerous",
        "severity": "HIGH"  # or "MEDIUM", "LOW"
    },
}
```

## Safety Design

- **Fail-open**: On error, the hook allows commands (prevents Claude from getting stuck)
- **Non-blocking**: Does not interfere with normal Claude operations
- **Minimal dependencies**: Uses only Python standard library

## Uninstallation

```bash
rm ~/.claude/hooks/pre_tool_use.py
rm ~/.claude/hooks/blocked.log  # Optional: remove logs
```

## Acceptance Criteria Met

- ✅ Hook follows Claude Code hooks format (~/.claude/hooks/)
- ✅ Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
- ✅ Logs every blocked attempt with timestamp, command, project path
- ✅ Displays clear message explaining why command was blocked
- ✅ Does not interfere with normal bash commands
- ✅ README with installation in 2 commands

## Resources

- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude-code/hooks)
- [Bounty Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## License

MIT

## Author

disillusi0n - Created for claude-builders-bounty Issue #3

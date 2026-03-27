# Dangerous Command Detector

> Claude Code hook that blocks dangerous bash commands before execution

## Overview

A pre-tool-use hook for Claude Code that intercepts and blocks dangerous bash commands to prevent accidental data loss or security issues.

## Features

- ✅ **Pattern Detection**: 10 dangerous patterns blocked
- ✅ **Logging**: All blocked attempts logged with timestamp and context
- ✅ **Clear Messages**: Explains why each command was blocked
- ✅ **Non-Intrusive**: Only blocks matching patterns, allows everything else

## Blocked Patterns

| Pattern | Severity | Description |
|---------|----------|-------------|
| `rm -rf` | Critical | Recursive force delete |
| `DROP TABLE/DATABASE` | Critical | SQL data destruction |
| `TRUNCATE` | Critical | Remove all table rows |
| `git push --force` | Critical | Force push to remote |
| `DELETE FROM` without WHERE | Critical | Delete all rows |
| Direct disk write (`>/dev/sdX`) | Critical | Filesystem corruption |
| `chmod 777` | High | Insecure permissions |
| `curl \| bash` | High | Remote code execution |
| `wget \| bash` | High | Remote code execution |
| `dd` to disk | Critical | Disk destruction |

## Installation

### 2 Commands

```bash
# 1. Install the hook
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/ljapptest-art/dangerous-hook/main/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py

# 2. Configure Claude Code
echo '{"hooks":{"pre_tool_use":["~/.claude/hooks/pre-tool-use.py"]}}' > ~/.claude/config.json
```

### Manual Installation

```bash
# Create hooks directory
mkdir -p ~/.claude/hooks

# Copy the hook script
cp pre-tool-use.py ~/.claude/hooks/

# Make executable
chmod +x ~/.claude/hooks/pre-tool-use.py

# Add to Claude Code config (~/.claude/config.json)
{
  "hooks": {
    "pre_tool_use": ["~/.claude/hooks/pre-tool-use.py"]
  }
}
```

## Usage

Once installed, the hook automatically blocks dangerous commands:

```
You: Run rm -rf /important-data

Claude: ⚠️ Dangerous Command Blocked
Command: rm -rf /important-data
Pattern: rm -rf
Reason: Recursive force delete can cause irreversible data loss
```

## Blocked Commands Log

All blocked attempts are logged to:

```
~/.claude/hooks/blocked.log
```

Format:
```json
{"timestamp": "2026-03-27T12:00:00", "command": "rm -rf data", "pattern": "rm -rf", "description": "...", "project_path": "/home/user/project"}
```

View recent blocks:
```bash
tail -f ~/.claude/hooks/blocked.log | jq .
```

## Testing

Test the hook with these safe examples:

```bash
# These will be blocked:
echo "Test: rm -rf should be blocked"
echo "Test: DROP TABLE should be blocked"
echo "Test: git push --force should be blocked"

# These will pass:
echo "Test: ls -la should pass"
echo "Test: git push origin main should pass"
echo "Test: rm single_file.txt should pass"
```

## Configuration

### Custom Patterns

Add patterns by editing `DANGEROUS_PATTERNS` in `pre-tool-use.py`:

```python
{
    "pattern": r"\byour_dangerous_command\b",
    "name": "Custom Command",
    "description": "Why this is dangerous",
    "severity": "critical"  # critical, high, medium
}
```

### Disable Hook

```bash
# Remove from config
jq 'del(.hooks.pre_tool_use)' ~/.claude/config.json > tmp.json && mv tmp.json ~/.claude/config.json
```

## Security Notes

- This hook is a safety net, not a security boundary
- Determined users can bypass it
- Always review commands before execution
- Keep backups of important data

## Compatibility

- Claude Code CLI
- Python 3.6+
- Linux, macOS, WSL

## License

MIT License

## Bounty

Created for [Claude Builders Bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) - $100

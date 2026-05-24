# Claude Code Dangerous Command Blocker

Pre-tool-use hook that intercepts and blocks destructive bash commands before execution.

## Installation

```bash
# 1. Clone this hook to your hooks directory
mkdir -p ~/.claude/hooks && curl -L https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use.sh

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## Blocked Patterns

- `rm -rf` — Destructive file deletion
- `DROP TABLE/DATABASE` — SQL destructive operations
- `git push --force` — Force push (overwrites history)
- `TRUNCATE` — SQL table truncation
- `DELETE FROM` without WHERE — SQL mass deletion

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Reason for blocking
- Attempted command
- Project path

## Testing

```bash
# Test with a dangerous command (should be blocked)
echo '{"tool": {"command": "rm -rf /tmp/test"}}' | ~/.claude/hooks/pre-tool-use.sh

# Test with a safe command (should pass)
echo '{"tool": {"command": "ls -la"}}' | ~/.claude/hooks/pre-tool-use.sh
```

## Author

OEN (@neosoong) — Created for claude-builders-bounty #3 ($100)

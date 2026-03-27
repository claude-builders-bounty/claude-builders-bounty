# Claude Code Pre-Tool-Use Hooks

## Installation

### Quick Install (One Command)

```bash
mkdir -p ~/.claude/hooks && cp -r hooks/* ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use/*.sh
```

### Manual Install

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy hooks
cp -r hooks/* ~/.claude/hooks/

# 3. Make scripts executable
chmod +x ~/.claude/hooks/pre-tool-use/*.sh
```

## Available Hooks

### `dangerous-command-guard.sh`

Blocks destructive commands before execution:

- `rm -rf /` - Deleting root filesystem
- `DROP TABLE/DATABASE/SCHEMA` - SQL destruction
- `TRUNCATE` - SQL table truncation
- `git push --force` - Force pushing to git
- `DELETE FROM` without WHERE clause - Deleting all rows

Blocked commands are logged to `~/.claude/hooks/blocked.log`.

## Hook Format Reference

Claude Code pre-tool-use hooks receive JSON on stdin:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /"
  }
}
```

And respond with JSON on stdout:

```json
{
  "decision": "block",
  "reason": "Dangerous command detected"
}
```

## Uninstall

```bash
rm -rf ~/.claude/hooks/pre-tool-use/dangerous-command-guard.sh
```

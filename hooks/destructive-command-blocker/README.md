# Claude Code Destructive Command Blocker Hook

A `PreToolUse` hook for Claude Code that intercepts and blocks dangerous bash commands (e.g., `rm -rf`, `DROP TABLE`, `git push --force`) before they are executed.

## Features

- **Robust Pattern Matching**: Detects recursive force deletes (`rm -rf`) even with separated flags (e.g., `rm -r -f`) or long flags (`--recursive --force`).
- **SQL Protection**: Blocks destructive SQL commands like `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- **Git Safety**: Prevents accidental force pushes to remote repositories.
- **Detailed Logging**: Logs all blocked attempts to `~/.claude/hooks/blocked.log` with timestamps and context.
- **Pure Python**: No external dependencies required.

## Installation (2 commands)

```bash
# 1. Download and install the hook
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py

# 2. Configure Claude Code to use the hook
echo '{"hooks": {"pre_tool_use": ["python3 ~/.claude/hooks/pre-tool-use.py"]}}' > ~/.claude/config.json
```

## How it works

When Claude attempts to use the `bash` tool, this hook script is executed first. It analyzes the command and returns a `deny` action if any destructive patterns are found, providing a clear explanation to Claude. If the command is safe, it returns an `allow` action.

### Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `--recursive --force` | Prevents irreversible data loss |
| `git push --force` / `-f` | Protects remote repository history |
| `DROP TABLE / DATABASE` | Prevents database destruction |
| `TRUNCATE` | Prevents mass data deletion |
| `DELETE FROM ...` (no `WHERE`) | Prevents mass row deletion |

## Logging

All blocked attempts are logged in JSON format to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-05-14T06:00:00Z", "command": "rm -rf /", "reason": "...", "project_path": "/path/to/project"}
```

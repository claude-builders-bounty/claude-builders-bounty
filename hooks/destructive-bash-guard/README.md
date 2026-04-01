# Destructive Bash Guard

This PreToolUse hook intercepts Claude Code before it executes Bash commands, actively blocking dangerous operations like `rm -rf`, unbounded SQL deletions, and git history rewrites. When a destructive command is detected, the hook securely terminates the operation, outputs a clear reason to Claude, and silently logs the intercepted attempt.

## Installation

Install the hook in exactly two steps.

**1. Copy the hook script**
```bash
cp hooks/destructive-bash-guard/guard.py ~/.claude/hooks/guard.py
```
*(Note: Ensure the `~/.claude/hooks` directory exists first by running `mkdir -p ~/.claude/hooks` if needed).* 

**2. Register in Claude Code settings**
Add the following snippet to your `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/guard.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

| Pattern | Description |
|---------|-------------|
| `rm -rf` | Blocks recursive forced deletion (handles all common flag variants) |
| `DROP TABLE` | Blocks destructive SQL table drops |
| `DROP DATABASE` | Blocks destructive SQL database drops |
| `TRUNCATE` | Blocks SQL table truncations |
| `DELETE FROM` (without `WHERE`) | Blocks unbounded SQL row deletions |
| `git push --force` | Blocks history rewriting pushes (including `--force-with-lease`) |
| `git reset --hard` | Blocks discarding uncommitted repository changes |

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log` in the following format:
```text
[2026-04-01T17:23:45Z] BLOCKED | pattern="rm -rf (recursive force delete)" | project="/home/user/myproject" | cmd="rm -rf ./build"
```

## Verification

You can manually verify the hook is working correctly by feeding it a mock tool payload:

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/dir"}, "cwd": "/tmp"}' | python3 ~/.claude/hooks/guard.py
```

**Expected Output (stderr):**
```text
BLOCKED: Destructive command detected
Pattern: rm -rf (recursive force delete)
Command: rm -rf /tmp/dir
Project: /tmp

This command has been blocked to prevent accidental data loss.
To proceed intentionally, use a safer alternative (e.g., move to trash, dry-run first).
```
*(The script will exit with status code `2` to instruct Claude Code to abort the tool execution).* 

## Requirements

- **Python:** 3.8+ 
- **Dependencies:** Standard library only (no external packages or tools required)
- **Platform:** macOS, Linux, and Windows (via Git Bash)

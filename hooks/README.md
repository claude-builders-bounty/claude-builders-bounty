# block-destructive-commands

A Claude Code `PreToolUse` hook that intercepts and blocks destructive bash commands before they execute.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive forced deletion — irreversible |
| `DROP TABLE` | Destroys table structure and all data |
| `git push --force` / `-f` | Rewrites remote history, can destroy others' work |
| `TRUNCATE TABLE` | Permanently removes all rows |
| `DELETE FROM` without `WHERE` | Deletes ALL rows from a table |

## Installation

**Option A: Python (cross-platform, recommended)**

```bash
cp hooks/block-destructive-commands.py ~/.claude/hooks/block-destructive-commands.py && chmod +x ~/.claude/hooks/block-destructive-commands.py
```

**Option B: Bash (Linux/macOS)**

```bash
cp hooks/block-destructive-commands.sh ~/.claude/hooks/block-destructive-commands.sh && chmod +x ~/.claude/hooks/block-destructive-commands.sh
```

Then add this to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-commands.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Claude Code fires `PreToolUse` before every Bash command
2. The hook reads the command JSON from stdin
3. It checks against destructive patterns using regex
4. If blocked: logs the attempt to `~/.claude/hooks/blocked.log` and returns a denial message to Claude
5. If safe: exits 0 and allows normal execution

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-09-05T12:00:00Z] BLOCKED | cwd=/home/user/project | reason=rm -rf detected | command=rm -rf /tmp/build
```

## Testing

```bash
# Should be BLOCKED (exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build"}}' | python3 ~/.claude/hooks/block-destructive-commands.py
echo "Exit code: $?"

# Should be BLOCKED (exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"DROP TABLE users"}}' | python3 ~/.claude/hooks/block-destructive-commands.py
echo "Exit code: $?"

# Should be BLOCKED (exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' | python3 ~/.claude/hooks/block-destructive-commands.py
echo "Exit code: $?"

# Should PASS (exit 0)
echo '{"tool_name":"Bash","tool_input":{"command":"npm test"}}' | python3 ~/.claude/hooks/block-destructive-commands.py
echo "Exit code: $?"

# Should PASS (exit 0) — DELETE with WHERE is safe
echo '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users WHERE id = 1"}}' | python3 ~/.claude/hooks/block-destructive-commands.py
echo "Exit code: $?"
```

## Requirements

- Python 3.6+ or Bash
- `jq` (for JSON parsing, bash version only)
- Python version uses only stdlib (`json`, `os`, `re`, `sys`)

## Log File

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:
- UTC timestamp
- Project working directory
- Reason for blocking
- The attempted command

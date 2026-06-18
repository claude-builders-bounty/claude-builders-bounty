# Claude Code Destructive Command Blocker 🔒

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) that intercepts and blocks destructive bash commands **before** they execute.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` | Recursive forced file deletion |
| `DROP TABLE` | SQL table destruction |
| `git push --force` | Force push overwrites remote history |
| `TRUNCATE` | SQL table data destruction |
| `DELETE FROM` (no `WHERE`) | Unconditional row deletion in SQL |

Safe commands pass through undisturbed.

## Installation

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
curl -sL -o ~/.claude/hooks/pre-tool-use/block_destructive_commands.py \
  https://raw.githubusercontent.com/Andyyook/claude-code-block-hook/main/block_destructive_commands.py
chmod +x ~/.claude/hooks/pre-tool-use/block_destructive_commands.py
```

Or copy manually:

```bash
cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use/
chmod +x ~/.claude/hooks/pre-tool-use/block_destructive_commands.py
```

## How It Works

1. Claude Code calls a hook event `PreToolUse` before every tool execution
2. The hook reads the tool call JSON from stdin
3. If the command matches a destructive pattern, it returns `permissionDecision: "deny"` with an explanation
4. Safe commands return `permissionDecision: "allow"` — zero interference

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-06-18T12:00:00Z", "command": "rm -rf /data", "reason": "rm -rf (recursive forced deletion)", "project_path": "/home/user/project"}
```

## Testing

To verify the hook is working:

```bash
# Should be blocked
echo '{"toolName":"Bash","toolInput":{"cmd":"rm -rf /tmp/test"}}' | python3 ~/.claude/hooks/pre-tool-use/block_destructive_commands.py

# Should be allowed
echo '{"toolName":"Bash","toolInput":{"cmd":"ls -la"}}' | python3 ~/.claude/hooks/pre-tool-use/block_destructive_commands.py

# Check the log
cat ~/.claude/hooks/blocked.log
```

## Requirements

- Python 3.7+
- Claude Code (any version that supports hooks)

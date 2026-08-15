# Pre-Tool-Use Hook — Block Destructive Bash Commands

Zero-dependency Python hook for **Claude Code** that intercepts dangerous
`Bash` tool calls before execution.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf`, `rm -f`, `rm -fr` | Force recursive / force delete |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE` | SQL table truncation |
| `git push --force` / `git push -f` | Force push to remote |
| `DELETE FROM table` (no `WHERE`) | Unqualified row deletion |

Commands with a proper `WHERE` clause (e.g., `DELETE FROM users WHERE id=1`) are **allowed**.

## Installation (2 commands)

```bash
# 1. Install the hook
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre_tool_use.py -o ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py

# 2. Register it in Claude Code settings
cat > ~/.claude/settings.json <<'EOF'
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/pre_tool_use.py"
      }]
    }]
  }
}
EOF
```

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:
- ISO timestamp
- Block reason
- Exact command
- Project working directory

## Testing

```bash
# Should BLOCK (exit 2 + log entry)
echo '{"tool_input":{"command":"rm -rf /tmp/test"}}' | python3 ~/.claude/hooks/pre_tool_use.py

# Should ALLOW (exit 0)
echo '{"tool_input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/pre_tool_use.py
```

## License

MIT
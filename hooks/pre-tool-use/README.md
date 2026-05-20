# Claude Code Security Hook - Block Destructive Commands

A pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 Commands)

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the hook
cp pre_tool_use_hook.py ~/.claude/hooks/
```

That's it! The hook will automatically protect your system.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete - dangerous |
| `DROP TABLE` | SQL destructive operation |
| `TRUNCATE` | SQL destructive operation |
| `DELETE FROM` without WHERE | SQL mass deletion |
| `git push --force` | Force push - can destroy history |
| `git push -f` | Force push variant |
| `:(){ :\|:& };:` | Fork bomb |

## How It Works

1. Intercepts bash commands before execution
2. Checks against a list of dangerous patterns
3. If matched:
   - Blocks the command
   - Logs to `~/.claude/hooks/blocked.log`
   - Returns clear error message to Claude

## Log Format

```
[2026-05-20 16:30:45] BLOCKED: "rm -rf /important/data" in /home/user/project
[2026-05-20 16:31:02] BLOCKED: "DROP TABLE users" in /home/user/project
```

## Example Usage

When Claude tries to run:
```bash
rm -rf node_modules
```

Hook blocks and returns:
```
🚫 BLOCKED: Potentially destructive command detected
Command: rm -rf node_modules
Reason: 'rm -rf' can cause irreversible data loss
Please use safer alternatives like: rm -r (without -f) or rmdir
```

## Testing

```bash
# Test the hook directly
python3 ~/.claude/hooks/pre_tool_use_hook.py

# Or test blocking
echo '{"tool_name": "bash", "tool_input": {"command": "rm -rf test"}}' | python3 ~/.claude/hooks/pre_tool_use_hook.py
```

## Customization

Edit `pre_tool_use_hook.py` to add your own dangerous patterns:

```python
DANGEROUS_PATTERNS = [
    r'rm\s+-rf',
    r'DROP\s+TABLE',
    # Add your patterns here
    r'your_custom_pattern',
]
```

## Safety Notes

- This hook is a safety net, not a replacement for careful command review
- Always understand commands before executing
- The hook logs all blocked attempts for audit purposes
- Disabled commands can be re-enabled by modifying the pattern list

## License

MIT
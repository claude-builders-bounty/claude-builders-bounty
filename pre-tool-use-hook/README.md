# Pre-tool-use Hook: Block Destructive Bash Commands

A Claude Code hook that intercepts and blocks dangerous bash commands before they execute.

## Install (2 commands)

```bash
# 1. Copy the hook
cp pre-tool-use-hook/hook.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py

# 2. Add to CLAUDE.md
echo 'hook = "pre-tool-use"' >> ~/.claude/CLAUDE.md
```

## What It Blocks

| Pattern | Why Blocked |
|---------|-------------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Irreversibly deletes table |
| `git push --force` | Overwrites remote history |
| `TRUNCATE TABLE` | Deletes all rows |
| `DELETE FROM table;` | No WHERE = deletes all data |

## Log Location

All blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Each entry includes: timestamp, command, project path, and reason.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use.py
# Remove hook line from ~/.claude/CLAUDE.md
```

## How It Works

The hook reads Claude Code's JSON payload from stdin, checks the bash command against dangerous patterns, and either:
- **Blocked**: Returns error JSON with reason, logs to `blocked.log`
- **Allowed**: Returns `{"continue": true}`

## Testing

```bash
# Test block
echo '{"tool": {"name": "Bash", "input": {"command": "rm -rf /"}}}' | python3 ~/.claude/hooks/pre-tool-use.py

# Test allow
echo '{"tool": {"name": "Bash", "input": {"command": "ls -la"}}}' | python3 ~/.claude/hooks/pre-tool-use.py
```
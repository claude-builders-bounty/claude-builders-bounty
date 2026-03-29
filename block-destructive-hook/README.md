# Block Destructive Bash Commands Hook

A `pre-tool-use` Claude Code hook written in Python that intercepts and blocks dangerous bash commands before they execute.

## Setup (2 Commands)

```bash
# Step 1: Copy hook to your Claude Code hooks directory
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/lam1688/claude-builders-bounty/main/block-destructive-hook/hook.py -o ~/.claude/hooks/pre-tool-use

# Step 2: Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

**Important:** The hook must be named `pre-tool-use` (no `.py` extension) and placed in `~/.claude/hooks/`.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Delete root filesystem |
| `rm -rf $HOME` | Delete home directory |
| `DROP TABLE` | SQL drop table |
| `TRUNCATE TABLE` | SQL truncate table |
| `DELETE FROM table;` (no WHERE) | Dangerous SQL delete |
| `git push --force` | Force push (rewrites history) |
| `git push -f` | Force push shortcut |

## What It Does

1. **Intercepts** every `Bash` tool call from Claude Code
2. **Checks** the command against dangerous patterns
3. **Blocks** matching commands and logs them
4. **Returns** a clear error message explaining what was blocked
5. **Allows** safe commands through without interference

## Log File

All blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Format:
```
[2026-03-29T18:00:00] BLOCKED | tool=Bash | project=/home/user/my-project | reason=Attempted to delete root filesystem
  Command: rm -rf / --no-preserve-root
```

## Exiting the Hook

If a command is blocked but you believe it's a false positive, you can:
1. Run the command directly in your terminal (bypassing Claude Code)
2. Temporarily move the hook file: `mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled`

## Requirements

- Python 3.6+
- Claude Code (with hooks support)

## License

MIT

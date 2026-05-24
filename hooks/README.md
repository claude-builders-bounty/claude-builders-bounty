# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code pre-tool-use hook that intercepts dangerous shell commands before
they execute and blocks them with a clear explanation.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` / `rm --recursive --force` | `rm -rf /important/dir` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM orders;` |
| `git push --force` / `-f` | `git push --force origin main` |

Normal commands pass through untouched — zero interference with your workflow.

## Install (2 commands)

```bash
# 1. Copy the hook to your Claude Code hooks directory
cp hooks/block-destructive.py ~/.claude/hooks/block-destructive.py

# 2. Register the hook in your Claude Code settings
claude hooks add pre-tool-use ~/.claude/hooks/block-destructive.py
```

### Alternative: project-level install

```bash
cp hooks/block-destructive.py .claude/hooks/block-destructive.py
claude hooks add pre-tool-use .claude/hooks/block-destructive.py
```

## How it works

1. Claude Code passes the pending tool call as JSON on **stdin**
2. The hook inspects `tool_name == "Bash"` commands only
3. Regex patterns detect destructive operations
4. Safe commands → **exit 0** (silent, no interference)
5. Dangerous commands → **exit 2** with a JSON message explaining the block
6. Every block is logged to `~/.claude/hooks/blocked.log` with timestamp,
   full command, working directory, and matched rules

## Log file

```
~/.claude/hooks/blocked.log
```

Example entry:

```
[2026-05-24T21:30:00Z] BLOCKED
  command : rm -rf node_modules
  path    : /home/user/project
  reasons : rm with recursive + force flags
```

## Testing

```bash
# Should block (exit 2)
echo '{"tool_name":"Bash","command":"rm -rf /tmp/test"}' | python3 hooks/block-destructive.py
echo $?  # 2

# Should allow (exit 0)
echo '{"tool_name":"Bash","command":"ls -la"}' | python3 hooks/block-destructive.py
echo $?  # 0

# Non-Bash tools pass through
echo '{"tool_name":"Read","command":"cat file.txt"}' | python3 hooks/block-destructive.py
echo $?  # 0
```

## Bypassing (when you really mean it)

Temporarily disable the hook in your Claude Code settings, run the command, then re-enable:

```bash
claude hooks remove pre-tool-use
# ... run your destructive command ...
claude hooks add pre-tool-use ~/.claude/hooks/block-destructive.py
```

---

MIT License — part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty) project.

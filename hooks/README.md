# Claude Code Hooks: Destructive Command Blocker

Pre-tool-use hook that blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/gacorpoll-ui/claude-builders-bounty/main/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
echo '{"hook": "pre-tool-use", "command": "python ~/.claude/hooks/pre-tool-use.py"}' >> ~/.claude/hooks.json
```

## What It Blocks

| Pattern | Why Blocked |
|---------|-------------|
| `rm -rf` | Can destroy entire directories |
| `rm -fr` | Same as above (variant) |
| `DROP TABLE` | Permanently deletes table + data |
| `TRUNCATE` | Removes all rows, can't rollback |
| `DELETE FROM` (no WHERE) | Deletes ALL rows |
| `git push --force` | Overwrites history (use `--force-with-lease`) |

## How It Works

1. Claude Code attempts to use Bash tool
2. Hook intercepts the command
3. Command pattern-checked against destructive patterns
4. If matched: **blocked** + logged to `~/.claude/hooks/blocked.log`
5. If safe: command proceeds normally

## Log Format

```
[2026-05-17T15:30:45] rm -rf | Command: rm -rf /tmp/test | Project: /home/user/project
[2026-05-17T15:31:02] git push --force | Command: git push --force origin main | Project: /home/user/repo
```

## Configuration

Edit `~/.claude/hooks/pre-tool-use.py` to customize patterns.

## Troubleshooting

**False positive?** The hook logs everything. Check `~/.claude/hooks/blocked.log` for the blocked command.

**Need to bypass?** Use the explicit flag approach (not recommended for regular use):
- For git: use `--force-with-lease` instead of `--force`
- For SQL: add WHERE clause (even `WHERE 1=1` if intentional)


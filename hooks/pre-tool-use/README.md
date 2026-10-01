# Block Destructive Bash Commands — Claude Code Hook

A `pre-tool-use` hook that prevents Claude Code from executing dangerous bash commands.

Blocks these patterns:
- `rm -rf /` (and variations)
- `DROP TABLE` / `DROP DATABASE`
- `git push --force`
- `TRUNCATE` without WHERE
- `DELETE FROM` without WHERE clause
- `sudo rm -rf`
- `chmod -R 777`
- Fork bombs and other destructive patterns

## Installation

```bash
# 2 commands:
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/block-destructive-commands.sh ~/.claude/hooks/pre-tool-use/
```

## How it works

1. Claude Code calls the hook before every bash command
2. The hook inspects the command for destructive patterns
3. Safe commands pass through unchanged
4. Blocked commands are:
   - Logged to `~/.claude/hooks/blocked.log` with timestamp and project path
   - Rejected with a clear explanation
   - Given instructions to temporarily disable if intentional

## Log format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-10-01T14:30:00Z] BLOCKED | project: /home/user/my-project | pattern: rm -rf\s+/ | command: rm -rf /
```

## Testing

To verify the hook works:

```bash
# Test: safe command should pass
echo '{"command": "ls -la"}' | bash hooks/pre-tool-use/block-destructive-commands.sh

# Test: destructive command should be blocked
echo '{"command": "rm -rf /"}' | bash hooks/pre-tool-use/block-destructive-commands.sh
# → exits with code 1, prints block message
```

## Uninstallation

```bash
rm ~/.claude/hooks/pre-tool-use/block-destructive-commands.sh
```

If you need to temporarily disable:

```bash
mv ~/.claude/hooks/pre-tool-use/block-destructive-commands.sh{,.disabled}
```
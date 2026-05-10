# 🛡️ Pre-Tool-Use Hook: Block Destructive Commands

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) `pre-tool-use` hook that intercepts and blocks dangerous shell commands before they can cause damage.

## Installation (one-liner)

```bash
mkdir -p ~/.claude/hooks && ln -sf "$(pwd)" ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` (destructive) | `rm -rf /` | Prevents accidental file deletion |
| `DROP TABLE` | `DROP TABLE users;` | Protects database schema |
| `TRUNCATE TABLE` | `TRUNCATE TABLE orders;` | Prevents data loss |
| `git push --force` | `git push origin main --force` | Use `--force-with-lease` instead |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Requires explicit scope |
| `chmod -R 777` | `chmod -R 777 /var/www` | Security risk |
| Direct disk writes | `echo data > /dev/sda1` | Filesystem protection |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2024-01-15 14:30:22] BLOCKED | command='rm -rf /tmp/cache' | reason='...' | pwd='/home/user/project'
```

## Testing

```bash
# Test that rm -rf is blocked
echo '{"command":"rm -rf /some/dir"}' | bash block-destructive-commands.sh
# → exit code 1, shows ❌ BLOCKED message

# Test that safe commands pass
echo '{"command":"rm file.txt"}' | bash block-destructive-commands.sh  
# → exit code 0 (allowed)

# Test that --force-with-lease is allowed
echo '{"command":"git push --force-with-lease origin main"}' | bash block-destructive-commands.sh
# → exit code 0 (allowed)

# Test that --force is blocked
echo '{"command":"git push --force origin main"}' | bash block-destructive-commands.sh
# → exit code 1 (blocked)

# Test DELETE FROM with and without WHERE
echo '{"command":"DELETE FROM users;"}' | bash block-destructive-commands.sh
# → exit code 1 (blocked)
echo '{"command":"DELETE FROM users WHERE id=1;"}' | bash block-destructive-commands.sh
# → exit code 0 (allowed)
```

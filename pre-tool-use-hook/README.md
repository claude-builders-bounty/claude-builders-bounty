# 🛡️ Pre-Tool-Use Hook: Block Destructive Bash Commands

A **zero-dependency** bash hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive shell commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
ln -sf "$(pwd)/block_destructive.sh" ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Example Matches |
|---------|----------------|
| **`rm -rf`** / **`rm -fr`** | `rm -rf /`, `rm -rf .git` |
| **`DROP TABLE` / `DROP DATABASE`** | SQL destructive operations |
| **`TRUNCATE TABLE`** | Mass deletion |
| **`DELETE FROM` (no WHERE)** | `DELETE FROM users` (unsafe) |
| **`git push --force` / `git push -f`** | Force push (rewrites history) |
| **`git commit --amend --no-edit`** | Silent history rewrite |
| **Disk wipes** | `dd if=`, `mkfs.*`, `>/dev/sd*` |
| **Fork bombs** | `:(){ :|: & };:` |
| **Recursive chmod/chown /** | `chmod -R 000 /` |
| **Pipe-from-URL shells** | `curl ... | sh`, `wget ... | sh` |

## How It Works

1. Claude Code calls this hook **before** every bash command
2. The hook reads the command from `stdin`
3. If it matches a dangerous pattern → **blocked** + logged
4. Safe commands pass through **unaffected**

## Logs

Blocked attempts are saved to `~/.claude/hooks/blocked.log`:

```
[2026-05-28 14:30:00] BLOCKED | /home/project | rm -rf /tmp/data
[2026-05-28 14:31:00] BLOCKED | /home/project | git push --force origin main
```

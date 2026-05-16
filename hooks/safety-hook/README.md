# Safety Hook — Pre-tool-use hook for Claude Code

Blocks destructive commands before they execute. **$100 bounty** from [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## Installation

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Category | Patterns |
|----------|----------|
| 🗑️ File Deletion | `rm -rf`, `rm -fr`, `mkfs.`, `dd if=/dev/zero` |
| 🛢️ Database | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without WHERE |
| 🔄 Git Force | `git push --force`, `git reset --hard`, `git clean -fd` |
| ⚙️ System | `shutdown`, `reboot`, `chmod -R 000`, `sudo rm` |
| 📦 Packages | `pip uninstall`, `npm uninstall`, `apt remove` |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-16 15:30:00] BLOCKED | reason=Recursive force delete | cwd=/project | cmd=rm -rf node_modules/
```

## How It Works

Claude Code calls `pre-tool-use` hooks before executing the `Bash` tool.
The hook receives the command as JSON on stdin and can return an error to block it.

# 🛡️ safe-shell-hook — Block Destructive Bash Commands in Claude Code

> A pre-tool-use hook for Claude Code that intercepts and blocks dangerous shell commands.

**Bounty:** [claude-builders-bounty/claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100 powered by Opire

---

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/davidsineri/claude-builders-bounty/main/submissions/safe-shell-hook/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

Done. Restart Claude Code — the hook is active.

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf /` | `rm -rf /` | Filesystem deletion |
| `rm -rf --no-preserve-root` | `rm -rf --no-preserve-root /` | Bypasses safety |
| `DROP TABLE/DATABASE` | `DROP TABLE users;` | Database destruction |
| `TRUNCATE` | `TRUNCATE orders;` | Data wipe |
| `git push --force` | `git push --force origin main` | History rewrite |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Mass deletion |

## How It Works

- Reads the tool call from stdin (Claude Code hook format)
- Checks if the command contains dangerous patterns
- Blocks with a clear error message and logs to `~/.claude/hooks/blocked.log`
- Passes through all safe commands untouched

## Logs

```
~/.claude/hooks/blocked.log
```

Format:
```
[2026-05-30 23:00:00] BLOCKED | dir=/project | cmd=rm -rf / | reason=rm -rf /
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## Requirements

- Claude Code (any version with hook support)
- `bash`, `python3`, `curl`

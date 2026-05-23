# cautious-claude — Pre-tool-use hook for Claude Code

> Blocks destructive bash commands before they execute. Never lose data to `rm -rf` again.

## Install (2 commands)

```bash
cp cautious-claude.sh ~/.claude/hooks/pre-tool-use.sh
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

That's it. Claude Code picks up hooks from `~/.claude/hooks/` automatically.

## What It Blocks

**Hard Block** (absolutely prevented, always):

| Pattern | Why |
|---------|-----|
| `rm -rf /` | Destroys entire filesystem |
| `rm -rf ~` | Destroys home directory |
| `rm -rf /*` | Destroys root contents |
| `mkfs.*` | Formats a disk |
| `dd if=/dev/zero` | Overwrites device |
| `> /dev/sda` | Redirects to block device |
| `:(){ :|:& };:` | Fork bomb |

**Warning Block** (dangerous, blocked with bypass option):

| Pattern | Why |
|---------|-----|
| `rm -rf` (any path) | Recursive force delete |
| `DROP TABLE` / `TRUNCATE` | Database table destruction |
| `DELETE FROM` (no WHERE) | Delete all rows without filter |
| `git push --force` / `-f` | Force push overwrites history |
| `chmod 777` | Opens world-writeable permissions |
| `chown -R` | Recursive ownership change |

## How It Works

Claude Code sends a JSON object to stdin before executing any tool:

```json
{"tool_name": "bash", "tool_input": "rm -rf /tmp/build", "cwd": "/home/user/project"}
```

The hook parses this, checks against block/warn patterns, and either:
- Returns `{"continue": true}` — command proceeds normally
- Returns `{"continue": false, "reason": "..."}` — command is stopped

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-23T18:30:00+0800] BLOCKED [CRITICAL] cmd="rm -rf /" project="/home/user/project"
[2026-05-23T18:31:00+0800] BLOCKED [WARNING] cmd="DROP TABLE users" project="/home/user/project"
```

## Bypass

Set the env var to bypass warning-level blocks:
```bash
export CLAUDE_ALLOW_DANGEROUS=true
```

Critical blocks (system-destroying commands) cannot be bypassed.

## License

MIT

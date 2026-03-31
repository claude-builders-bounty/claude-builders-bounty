# Pre-Tool-Use Guard Hook 🔒

A Claude Code safety hook that intercepts and blocks dangerous bash commands before execution.

## What It Blocks

| Pattern | Severity | Example |
|---------|----------|---------|
| `rm -rf /` | CRITICAL | Recursive force delete from root |
| `DROP TABLE` | CRITICAL | SQL table destruction |
| `TRUNCATE` | HIGH | SQL data wipe |
| `DELETE FROM` (no WHERE) | HIGH | Unconditional SQL delete |
| `git push --force` | HIGH | Force push (non-reversible) |
| `git reset --hard` | MEDIUM | Discards local changes |
| `chmod 777` | MEDIUM | Insecure permissions |
| `curl \| sh` | HIGH | Arbitrary code execution |
| Fork bomb | CRITICAL | System resource exhaustion |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/hopkdj/claude-builders-bounty/feat/pre-tool-use-hook-3/hooks/pre_tool_use_guard/pre_tool_use_guard.py -o ~/.claude/hooks/pre_tool_use_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

Or manually:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre_tool_use_guard/pre_tool_use_guard.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

## How It Works

1. Claude Code calls the hook before executing any bash command
2. The hook checks the command against known dangerous patterns
3. If matched → blocks the command and logs the attempt
4. If safe → exits 0, allowing execution

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- Severity level
- Pattern name
- Attempted command
- Project directory

## Features

- ✅ 15+ dangerous pattern detections
- ✅ Severity levels (CRITICAL / HIGH / MEDIUM)
- ✅ Audit logging to `~/.claude/hooks/blocked.log`
- ✅ Clear error messages explaining why commands were blocked
- ✅ Zero dependencies (Python 3 stdlib only)
- ✅ Non-intrusive — only blocks known dangerous patterns

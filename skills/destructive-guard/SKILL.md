---
name: destructive-guard
description: Pre-tool-use hook that blocks destructive bash commands. Intercepts rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE FROM without WHERE before execution.
argument-hint: ""
---

# Destructive Command Guard

A Claude Code `pre-tool-use` hook that intercepts dangerous commands before they execute.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm -r` / `rm -f` | Recursive force delete |
| `git push --force` / `git push -f` | Force push to remote |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE [TABLE]` | SQL table truncation |
| `DELETE FROM x` (no WHERE) | Mass data deletion |
| `> /dev/sda` | Raw block device overwrite |
| `chmod 777` | World-writable permissions |
| `:(){ :\|:& };:` | Fork bomb |
| `dd if=` | Raw disk copy |

## Installation

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Behavior

- **Non-zero exit (2)** → tool call is blocked, command never executes
- **Exit 0** → passes through unmodified
- Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with UTC timestamp

## Verification

```bash
# Test that it blocks rm -rf
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 hooks/pre-tool-use
# → exits with code 2, logs to blocked.log

# Test that safe commands pass through
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre-tool-use
# → exits 0, outputs unchanged JSON
```

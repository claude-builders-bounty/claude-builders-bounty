# Claude Code Pre-Tool-Use Hook: Destructive Command Blocker

**Bounty: $100** — Closes #1468

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## Installation

### 1. Install the hook

```bash
# Create the hooks directory (if it doesn't exist)
mkdir -p ~/.claude/hooks

# Copy the hook script
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use

# Make it executable
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. Two commands. Claude Code automatically discovers and runs hooks from `~/.claude/hooks/`.

### 2. Verify it's working

```bash
# Check the hook is executable
ls -la ~/.claude/hooks/pre-tool-use

# Run a test (should pass through normally)
~/.claude/hooks/pre-tool-use bash "ls -la"
echo $?  # Should be 0

# Test blocking (should block)
~/.claude/hooks/pre-tool-use bash "rm -rf /tmp/test"
echo $?  # Should be 1
```

## What it blocks

| Pattern | Example | Severity |
|---|---|---|
| `rm -rf` (or flags containing r and f) | `rm -rf /tmp/data` | Critical |
| `DROP TABLE` | `DROP TABLE users` | Critical |
| `DROP DATABASE` | `DROP DATABASE production` | Critical |
| `git push --force` | `git push origin main --force` | High |
| `TRUNCATE` | `TRUNCATE users` | High |
| `DELETE FROM` without WHERE | `DELETE FROM users` | High |
| `dd if=` | `dd if=/dev/zero of=/dev/sda` | High |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Critical |
| `rm /` (on root) | `rm -rf /` | Critical |

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log` in JSON format.

## Customization

Edit `hooks/pre-tool-use` to add new blocked patterns or modify existing ones.

## How it works

Claude Code hooks follow this protocol:
- Each hook is an executable in `~/.claude/hooks/`
- `pre-tool-use` hooks receive: the tool name and its arguments
- Exit code 0 = allow, Exit code 1 = block

This hook is written in Python 3 with zero external dependencies (stdlib only).

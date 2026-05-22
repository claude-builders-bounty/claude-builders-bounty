---
name: pre-tool-use-safety
description: Claude Code PreToolUse hook that blocks destructive bash commands (rm -rf, DROP TABLE, force push, TRUNCATE, DELETE without WHERE, etc.) before they execute. Logs every blocked attempt with timestamp and project path.
version: 1.0.0
---

# Pre-Tool-Use Safety Hook

This is a `PreToolUse` hook for Claude Code that intercepts dangerous shell commands before they run.

## How It Works

1. Claude Code sends JSON via stdin with `tool_name`, `tool_input.command`, and `cwd`
2. Hook checks if `tool_name == "Bash"` — if not, passes through silently
3. Extracts the command string and compares (case-insensitively) against destructive patterns
4. **If matched**: writes to `~/.claude/hooks/blocked.log` and returns a `permissionDecision: "deny"` JSON
5. **If safe**: exits 0 with no output (command proceeds normally)

## Why a Hook (Not a Setting)

Claude Code's `settings.json` permissions are coarse-grained — they allow/deny entire tools or command prefixes. This hook adds **semantic awareness**:

- It distinguishes `DELETE FROM users WHERE id=1` (safe) from `DELETE FROM users` (dangerous)
- It catches flag-order variations (`rm -rf` vs `rm -fr`)
- It logs an audit trail of every blocked attempt — useful for security review

## Installation

See [README.md](./README.md).

## Files

| File | Purpose |
|------|---------|
| `hook.sh` | The hook script (executable bash) |
| `README.md` | Install instructions in 2 commands |
| `examples/blocked-log-sample.log` | Sample log output |
| `examples/claude-message-sample.md` | What Claude sees when a command is blocked |
| `tests/test-hook.sh` | 17 test cases (10 dangerous, 7 safe) |

---
name: safety-guard
description: Safety hook that checks bash commands for destructive patterns before execution. Use to prevent accidental system damage.
---

# Safety Guard Hook

This skill acts as a protective layer for Gemini CLI, intercepting shell commands and checking them against a list of known destructive patterns (e.g., `rm -rf /`, `mkfs`, fork bombs).

## How it works

When a user or Gemini proposes a shell command that matches a destructive pattern, the hook will flag it and require explicit user confirmation.

## Destructive Patterns Blocked
- Recursive root deletion (`rm -rf /`)
- Filesystem creation (`mkfs`)
- Low-level disk writes (`dd` to block devices)
- Fork bombs
- Dangerous root permissions changes

## Implementation

The skill uses `scripts/check_command.cjs` to validate strings.

## Workflow

1.  **Intercept**: Before running a shell command, the agent should run `node scripts/check_command.cjs "<command>"`.
2.  **Warn**: If the script exits with code 1, the agent MUST warn the user:
    - "⚠️ This command is potentially destructive. Are you sure you want to proceed?"
3.  **Log**: Blocked attempts should be mentioned in the session history.

# Destructive Command Guard for Claude Code

A PreToolUse hook that blocks dangerous Bash commands before they are executed.

## Blocked Commands

This hook blocks:

- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without a WHERE clause

## Installation

Run:

bash install.sh

The installer places the hook in:

~/.claude/hooks/destructive-command-guard.py

and configures it as a Claude Code PreToolUse hook for Bash.

## Logging

Every blocked command is logged to:

~/.claude/hooks/blocked.log

Each log entry contains:

- Timestamp
- Attempted command
- Project path
- Matched blocking rule

## Behavior

When a destructive command is detected, the hook returns:

permissionDecision: deny

with a clear explanation describing why the command was blocked.

Normal Bash commands are not affected.

## Tests

The included tests verify all required destructive patterns and confirm that normal Bash commands continue to work.

## Bounty

Submission for:

claude-builders-bounty/claude-builders-bounty#3

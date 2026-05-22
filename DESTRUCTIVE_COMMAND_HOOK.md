# Destructive Command Blocker Hook

This is a Claude Code pre-tool-use hook for Bash. It blocks dangerous commands before they run and logs every blocked attempt to ~/.claude/hooks/blocked.log.

## Blocks

- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without a WHERE clause

## Install

Run these two commands from the repository root:

    mkdir -p ~/.claude/hooks && cp .claude/hooks/destructive-command-blocker.py ~/.claude/hooks/destructive-command-blocker.py
    cp .claude/settings.example.json ~/.claude/settings.json

## Behavior

The hook reads Claude Code pre-tool-use JSON from stdin, checks Bash commands, and returns Claude Code's documented hookSpecificOutput JSON with permissionDecision: "deny" when a command should be blocked. The denial reason explains why the command was blocked so Claude can revise its action. Normal Bash commands exit 0 with no output and are not logged.

Blocked attempts are logged as CSV with:

- timestamp
- attempted command
- project path
- reason

## Validate

    python test_destructive_command_blocker.py

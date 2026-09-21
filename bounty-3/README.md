# Claude Code destructive-command guard

A PreToolUse hook for Claude Code that intercepts Bash calls before execution and denies destructive commands while leaving normal shell commands untouched.

## What it blocks

- rm -rf / rm -fr
- DROP TABLE
- git push --force, force variants, and git push -f
- TRUNCATE
- DELETE FROM statements that do not contain a WHERE clause

Every blocked attempt is appended as JSON Lines to ~/.claude/hooks/blocked.log with an ISO-8601 UTC timestamp, attempted command, project path, and block reason. Claude receives a clear denial reason so it can choose a safer alternative.

## Install in two commands

    git clone https://github.com/naro8259/claude-builders-bounty.git && cd claude-builders-bounty/bounty-3
    python3 install.py

The installer copies the hook to ~/.claude/hooks/destructive_command_guard.py and safely adds a PreToolUse matcher for Bash to ~/.claude/settings.json without deleting existing settings.

Restart Claude Code after installation.

## Verify

    python3 -m unittest discover -s tests -v

You can also exercise the hook protocol directly:

    echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}' | python3 destructive_command_guard.py

The result contains permissionDecision set to deny. A safe command such as git status produces no hook output and follows Claude Code's normal permission flow.

## Design notes

The hook uses Claude Code's structured PreToolUse response instead of relying on exit-code-only blocking. It only inspects the Bash tool and returns no decision for commands it does not care about. This keeps ordinary Bash usage unchanged while providing explicit feedback on denied calls.

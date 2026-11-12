# Claude Code destructive-command safety hook

A Python standard-library-only PreToolUse hook that denies the destructive Bash operations specified in bounty #3:

- rm with both recursive and force flags, including split and long-option forms
- git push --force, -f, and --force-with-lease
- SQL DROP TABLE, TRUNCATE, and DELETE FROM without WHERE

Every denied attempt is appended to ~/.claude/hooks/blocked.log as JSON Lines with an ISO-8601 UTC timestamp, attempted command, project path, and denial reason. Safe commands pass through without a decision override.

## Install

From this directory, run:

    python3 install.py

The installer copies the hook into ~/.claude/hooks/ and merges a Bash PreToolUse entry into ~/.claude/settings.json. Existing settings and hook entries are preserved; repeated installation does not add duplicate entries.

Restart Claude Code after installation.

## Test

    python3 -m unittest -v test_hook.py

The tests run offline and cover dangerous command variants, safe commands, the Claude Code deny response, and the audit log.

## Behavior

The hook reads the Claude Code hook payload from stdin. For blocked commands it emits a PreToolUse permissionDecision: deny response with a reason Claude can explain. It does not execute commands or modify project files.

This is a defensive guardrail, not a complete shell or SQL parser. Review commands with complex shell expansion, generated SQL, aliases, or indirect execution paths before relying on it as a security boundary.

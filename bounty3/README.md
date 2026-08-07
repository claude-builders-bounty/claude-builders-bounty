# Destructive-command safety hook

AI-assisted deliverable for the $100 bounty in [issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

The Python hook implements the current Claude Code PreToolUse JSON contract. It blocks recursive-force removal, forced Git pushes, DROP TABLE, TRUNCATE, and DELETE FROM statements that have no WHERE clause. It logs each blocked attempt as one JSON line with a UTC timestamp, attempted command, project path, and matching reasons. Ordinary commands exit silently so the normal Claude Code permission flow continues.

## Installation

1. mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/
2. Merge settings.example.json into ~/.claude/settings.json, keeping any existing hooks.

On Windows, use the Python executable available in the user’s PATH in the command field. The script itself uses pathlib, so the log path resolves to the current user’s .claude/hooks/blocked.log directory.

## Verification

Run python tests/test_hook.py. The test suite pipes real Claude Code-style JSON payloads into the hook and checks deny decisions, reason messages, JSONL logs, timestamp format, project path, malformed input, tool filtering, SQL WHERE exceptions, shell variants, and normal-command non-interference.

## AI disclosure

This deliverable was created with AI assistance. A human contributor should review the matching policy, run the hook with their installed Claude Code version, and disclose AI use in the pull request if required.

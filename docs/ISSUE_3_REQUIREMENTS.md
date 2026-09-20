# Issue #3 requirement snapshot (offline)

Source reference: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

This document summarizes the issue content previously retrieved in the task
conversation. The user subsequently supplied a local repository ZIP and required
all implementation and validation to remain offline. No issue page or other
network resource was accessed during this implementation. The ZIP contains only
README.md and LICENSE; it does not contain the issue body or Git history.

## Acceptance criteria carried forward

1. Provide a Python or Bash command hook for Claude Code's PreToolUse event.
2. Refuse recursive forced removal, forced Git pushes, table drop/truncation,
   and DELETE FROM statements lacking a WHERE condition.
3. Record each blocked attempt in ~/.claude/hooks/blocked.log with a timestamp,
   the attempted command, and the project path.
4. Explain a refusal clearly to Claude while permitting ordinary Bash use.
5. Document installation in at most two commands.

## Implementation choices

- Python standard library only, targeting macOS/Linux with Python 3.9+.
- Parse input text without executing it; inspect common literal command forms.
- Use exit 2 plus stderr to block a PreToolUse call; exit 0 to continue.
- Store private, append-only JSONL audit records and refuse despite audit errors.
- Preserve existing Claude settings with a local installer and backups.
- Test only in temporary HOME directories, using command strings as test data.

These choices are a local defensive implementation. No bounty has been claimed,
no live Claude session has been tested, and nothing has been posted or submitted.

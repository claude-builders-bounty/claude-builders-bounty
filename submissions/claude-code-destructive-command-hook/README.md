# claude-hook: block destructive Bash commands

A Claude Code `PreToolUse` hook that blocks destructive shell commands before they run, logs every blocked attempt, and explains why.

## Install (1 command)

```bash
python3 install.py
```

Then restart Claude Code (or reload hooks). The installer copies the hook to `~/.claude/hooks/` and merges the `PreToolUse` entry into `~/.claude/settings.json` without touching your other settings.

## What it blocks

- `rm -rf` (also `-fr`, `-r -f`, and similar flag combinations)
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as one JSON line with timestamp, command and working directory. The hook exits with code 2, which Claude Code treats as a block, and prints a clear message to stderr.

## Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"}}' | python3 block_dangerous_bash.py; echo "exit=$?"
printf '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 block_dangerous_bash.py; echo "exit=$?"
```

Expected: first exits 2, second exits 0. To use a custom log path in tests, set `CLAUDE_HOOK_LOG=/tmp/blocked.log`.

## Design notes

- The hook only inspects; it never executes the command.
- Malformed JSON or non-Bash tools are allowed through so normal work is not broken.
- If logging fails, the hook still blocks (it never fails open on a dangerous command).

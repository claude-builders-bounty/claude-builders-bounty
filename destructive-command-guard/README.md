# Destructive Command Guard

A dependency-free Python `PreToolUse` hook for Claude Code. It denies the five
command classes in bounty #3, writes a JSON Lines audit record to
`~/.claude/hooks/blocked.log`, and returns the current Claude Code structured
denial response. Normal Bash calls produce no output and continue unchanged.

## Install (one command)

From this directory:

```bash
python3 install.py
```

Restart Claude Code after installation. The installer copies the hook to
`~/.claude/hooks/` and safely merges its `PreToolUse` entry into
`~/.claude/settings.json` without replacing unrelated settings.

## Test (one command)

```bash
python3 -m unittest -v test_destructive_command_guard.py
```

Blocked attempts are logged with an ISO-8601 UTC timestamp, attempted command,
project path, and reason. The log is created with mode `0600`.

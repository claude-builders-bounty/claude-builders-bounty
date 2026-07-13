# Claude Code pre-tool-use safety hook

This bounty deliverable adds a Claude Code `pre-tool-use` hook that blocks destructive shell commands before they run.

## Install in two commands

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add the hook to your Claude Code hook configuration as a `pre-tool-use` hook for bash/shell tool calls.

## Behavior

The hook blocks commands that match these destructive patterns:

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push -f`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with:

- timestamp
- attempted command
- project path
- matched safety rule

Allowed commands exit with status `0` and do not write a log entry. Blocked commands exit with status `2` and print a clear message for Claude explaining why the command was blocked.

## Input format

Claude Code hooks pass JSON on stdin. This hook accepts common command shapes, including:

```json
{"tool_name":"bash","tool_input":{"command":"rm -rf dist"},"cwd":"/repo"}
```

It also supports `bash`, `cmd`, `script`, and top-level `command` fields for compatibility with small local wrappers.

## Local validation

Run:

```bash
python3 test_block_destructive_bash.py
```

The tests cover blocked commands, safe commands, and `DELETE FROM` with and without a `WHERE` clause.

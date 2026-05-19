# Block destructive Bash commands

This Claude Code `pre-tool-use` hook blocks risky Bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/block_destructive_bash.py ~/.claude/hooks/pre-tool-use/block_destructive_bash.py && chmod +x ~/.claude/hooks/pre-tool-use/block_destructive_bash.py
```

Register the copied script in your Claude Code hook configuration for Bash `pre-tool-use` events.

## Blocked patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Normal Bash commands pass through without output.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes an ISO-8601 UTC timestamp, block reason, project path, and attempted command.

## Manual test

```bash
printf '%s\n' '{"tool_name":"Bash","cwd":"/tmp/example-project","tool_input":{"command":"rm -rf /tmp/example"}}' \
  | python3 hooks/pre-tool-use/block_destructive_bash.py
```

Expected result: non-zero exit and a clear `Blocked dangerous bash command` message.

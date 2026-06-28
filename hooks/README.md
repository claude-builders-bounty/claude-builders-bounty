# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they
run.

## Install

```sh
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
python3 -m json.tool > ~/.claude/settings.json <<'JSON'
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block_destructive_bash.py"}]}]}}
JSON
```

## What It Blocks

- `rm -rf` and equivalent `rm -fr` forms
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Normal Bash commands return `permissionDecision: allow` and continue unchanged.
Blocked commands return `permissionDecision: deny` with a clear reason for
Claude.

## Blocked Attempt Log

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- UTC timestamp
- attempted command
- project path
- blocked reason

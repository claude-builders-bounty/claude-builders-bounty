# Destructive Bash Blocker Hook

Claude Code `pre-tool-use` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/block_destructive_bash.py"}]}]}}
```

Add the JSON to your Claude Code settings file.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- timestamp
- attempted command
- project path
- matched rule

Normal Bash commands pass through unchanged.

## Example Blocked Log Entry

```json
{"timestamp":"2026-06-21T07:45:00.000000+00:00","project_path":"/repo","rule":"recursive force delete","command":"rm -rf dist"}
```

## Exit Codes

- `0`: command is allowed
- `2`: command is blocked

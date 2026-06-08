# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they
run and records every blocked attempt in `~/.claude/hooks/blocked.log`.

## Install

From this repository root:

```bash
python hooks/install.py
```

That command copies `hooks/block_destructive_bash.py` into
`~/.claude/hooks/` and merges the Bash `PreToolUse` hook into
`~/.claude/settings.json`. If you prefer a manual install, copy the hook file to
`~/.claude/hooks/` and merge `hooks/settings.example.json` into your Claude Code
settings.

## Blocked Patterns

- `rm -rf`, `rm -fr`, and split recursive force variants such as `rm -r -f`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Allowed Bash commands produce no output, so the normal Claude Code permission
flow continues unchanged. Blocked commands return a `permissionDecision: deny`
message explaining why the command was rejected.

## Test

```bash
python -m unittest discover -s tests -v
```

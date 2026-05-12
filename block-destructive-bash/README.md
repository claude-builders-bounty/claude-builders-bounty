# Block Destructive Bash Hook

Claude Code `PreToolUse` hook that denies dangerous Bash commands before execution and logs each blocked attempt.

## Install

From this directory:

```bash
mkdir -p ~/.claude/hooks && cp block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

Add the `PreToolUse` entry from `settings-example.json` to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent `rm -fr` option combinations
- `git push --force` and `git push -f`
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- SQL `DELETE FROM ...` statements without a `WHERE` clause

Normal Bash commands exit successfully without output, so Claude Code continues as usual.

## Log Format

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines:

```json
{"timestamp":"2026-05-12T10:00:00Z","project_path":"/path/to/project","command":"rm -rf build","reason":"Blocked destructive rm command with recursive and force flags"}
```

## Test

```bash
python3 -m unittest test_block_destructive_bash.py
```


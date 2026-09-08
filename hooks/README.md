# Block destructive bash commands

Claude Code `PreToolUse` hook that stops recursive force-delete, force-pushes, and unscoped SQL before they run.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
bash hooks/install.sh
```

Run from this repository (or copy `hooks/` first). `install.sh` copies the hook to `~/.claude/hooks/block-destructive.py` and registers it in `~/.claude/settings.json`.

## What it blocks

| Pattern | Example |
|---|---|
| Recursive force-delete | `rm` with both recursive and force flags |
| Force push | `git push --force`, `git push -f origin main` |
| Schema drop | DROP TABLE statements |
| Unscoped wipe | TRUNCATE statements |
| Unscoped delete | DELETE FROM without WHERE |

Scoped deletes, ordinary `git push`, `git push --force-with-lease`, and `rm file` / `rm -f file` are allowed.

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as:

```
<utc-timestamp>	<project-path>	<command>
```

Claude sees a stderr message explaining why the tool call was denied (hook exit code 2).

## Test

```bash
python3 tests/test_block_destructive.py
```

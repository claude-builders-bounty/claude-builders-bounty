# Block Destructive Commands Hook 🛡️

A Claude Code `pre-tool-use` security hook that intercepts bash commands before execution and blocks potentially destructive operations.

---

## Blocked Operations

- ❌ **Recursive deletions**: `rm -rf`, `rm -fr`, `rm --recursive --force`
- ❌ **Table drops & truncations**: `DROP TABLE`, `TRUNCATE TABLE`, `TRUNCATE`
- ❌ **Unrestricted deletions**: `DELETE FROM <table>` (without a `WHERE` clause)
- ❌ **Force pushes**: `git push --force`, `git push -f`, `git push +ref`
- ❌ **Disk destruction / Fork bombs**: `mkfs`, `fdisk`, `dd of=/dev/...`, `:(){:|:&};:`

All blocked executions are appended to `~/.claude/hooks/blocked.log` with timestamp, project directory, and exact command string.

---

## Installation (2 Commands)

```bash
# 1. Create Claude hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy hook script and make executable
cp hooks/block-destructive-commands/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

---

## Testing

Run the automated test suite:
```bash
python hooks/block-destructive-commands/tests/test_hook.py
```

# Destructive Command Blocker — Claude Code Hook

Pre-tool-use hook that blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block_destructive.py ~/.claude/hooks/pre_tool_use
chmod +x ~/.claude/hooks/pre_tool_use
```

## What It Blocks

### File System
- `rm -rf` / `rm -r /` — Recursive force deletes
- `chmod -R 000` — Permission removal
- `dd if=/dev/zero` — Zero-fill destruction
- `mkfs`, `mkswap` — Filesystem creation

### Database
- `DROP TABLE / DATABASE / SCHEMA` — Object deletion
- `TRUNCATE` — Row removal
- `DELETE FROM` without `WHERE` — Missing clause
- `UPDATE ... SET` without `WHERE` — Missing clause
- `ALTER TABLE ... DROP` — Column/table removal

### Git
- `git push --force` / `-f` — History overwrite
- `git reset --hard` — Uncommitted change loss
- `git clean -fd` — Untracked file removal
- `git rebase --interactive` — History rewrite

### System
- `shutdown`, `reboot`, `halt`, `poweroff` — System interruption
- `init 0` / `init 6` — Runlevel change

### Infrastructure
- `kubectl delete namespace` — Resource destruction
- `docker rm -f` / `docker system prune -f` — Container/image removal
- `terraform destroy` — Infrastructure teardown

## Features

- **Detailed logging** — Every blocked command is logged to `~/.claude/hooks/blocked.log` with timestamp, project path, and command
- **Clear error messages** — Claude sees exactly why the command was blocked
- **Normal commands unaffected** — Only matching destructive patterns are blocked
- **Portable** — Pure Python 3, no dependencies beyond standard library

## Bounty

Part of [Bounty #3 — $100](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

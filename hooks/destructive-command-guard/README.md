# Destructive Command Guard

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Install

```bash
bash install.sh
```

That's it. The hook is now active in Claude Code.

## What It Blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, recursive `rm` on broad paths (`/`, `~`, `*`, `..`) |
| **SQL** | `DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **Git** | `push --force`, `reset --hard`, `clean -fd` |
| **System** | `mkfs`, `dd` to devices, `chmod -R 777 /`, fork bombs |
| **Docker** | `docker system prune -a` |

## What It Allows

Normal commands pass through without interference:

- `rm file.txt` — single file deletion
- `rm -r ./node_modules` — targeted directory removal
- `DELETE FROM users WHERE id = 5` — scoped SQL deletes
- `git push origin main` — normal pushes
- `docker build`, `docker system prune` (without `-a`) — safe Docker ops

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` as JSON:

```json
{"timestamp": "2026-04-04T18:00:00Z", "command": "rm -rf /", "reason": "rm -rf: recursive forced deletion", "project_path": "/home/user/project"}
```

## Testing

```bash
python3 test_guard.py
```

Runs 43 test cases (22 blocked + 21 allowed).

## How It Works

1. Claude Code calls the hook before executing any bash/shell tool
2. The hook receives the tool-use event as JSON on stdin
3. It checks the command against 16 regex patterns
4. If matched: logs the attempt, prints a structured error, exits with code 2 (blocks execution)
5. If safe: exits with code 0 (allows execution)

## Files

- `guard.py` — The hook (drop into `~/.claude/hooks/pre-tool-use/`)
- `install.sh` — One-command installer
- `test_guard.py` — Comprehensive test suite
- `README.md` — This file

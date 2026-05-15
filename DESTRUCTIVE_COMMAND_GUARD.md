# Destructive Command Guard

A Claude Code pre-tool-use hook that blocks destructive bash commands before they can execute. Zero dependencies, Python 3.7+.

## What it blocks

| Pattern | Example | Safe Alternative |
|---------|---------|-----------------|
| `rm -rf` / `rm -r -f` | `rm -rf /var/cache` | Use `mv <path> /tmp/trash/` |
| `git push --force` / `git push -f` | `git push --force origin main` | Use `git push --force-with-lease` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Backup first, use `RENAME TO <table>_backup` |
| `TRUNCATE` | `TRUNCATE logs;` | Use `DELETE` with a `WHERE` clause |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Always add a `WHERE` clause |
| `dd` to block devices | `dd if=/dev/zero of=/dev/sda` | Double-check the `of=` target |
| `chmod -R 777` | `chmod -R 777 /var/www` | Use specific perms (755/644) |
| `chown -R` (recursive) | `chown -R root:root /usr` | Target specific paths |
| Direct disk writes | `echo data > /dev/sda` | Never write directly to block devices |
| `mkfs` / `format` | `mkfs.ext4 /dev/sdb1` | Triple-check the device |
| Fork bombs | `:(){ :\|:& };:` | Never run fork bombs |
| `shred` | `shred -n 3 secret.doc` | Shredding is irreversible |

## Installation

**2 commands:**

```bash
# 1. Copy the hook to your Claude Code hooks directory
mkdir -p .claude/hooks/pre-tool-use && cp hooks/pre-tool-use/destructive-command-guard.py .claude/hooks/pre-tool-use/

# 2. Make it executable
chmod +x .claude/hooks/pre-tool-use/destructive-command-guard.py
```

That's it. Every Claude Code session in this project will now block dangerous commands automatically.

## Usage

Once installed, the hook runs silently for every tool call. When it blocks a command, you'll see:

```
╔══ BLOCKED BY DESTRUCTIVE COMMAND GUARD ══╗
  Pattern:  Recursive force delete (RM_RF)
  Command:  rm -rf /var/cache
  Project:  /home/user/my-project
  Time:     2026-05-15T12:30:00+00:00
  Suggestion: Use a trash/bin directory instead of rm -rf
  Logged to: /home/user/.local/share/destructive-command-guard/guard.log
╚════════════════════════════════════════════╝
```

### Log files

All blocked attempts are logged to:
- `$DESTRUCTIVE_GUARD_LOG` (if set)
- `~/.local/share/destructive-command-guard/guard.log` (default — XDG compliant)
- Each entry is a JSON line: `timestamp`, `command`, `matched_pattern`, `description`, `project_path`, `suggestion`

## How it works

The hook intercepts every bash tool call made by Claude Code. It:
1. Normalizes the command (strips comments, skips `echo`)
2. Checks against a curated list of destructive patterns
3. **Blocks + logs** if matched, **passes through** if safe

## Testing

```bash
python3 -m pytest test_guard.py -v
```

All 30 tests should pass — covering every dangerous pattern, safe commands, edge cases, and logging.

## Files

```
hooks/pre-tool-use/destructive-command-guard.py  — main hook script
DESTRUCTIVE_COMMAND_GUARD.md                     — this file
test_guard.py                                     — 30 unit tests
```

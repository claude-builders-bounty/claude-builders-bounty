# Destructive Command Blocker

Pre-tool-use hook for Claude Code that blocks dangerous bash commands before execution.

## Quick Install (2 Commands)

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/block_destructive_commands.py https://raw.githubusercontent.com/afu20260324/claude-builders-bounty/main/safe-bash-hook/block_destructive_commands.py && chmod +x ~/.claude/hooks/block_destructive_commands.py
```

**Or manually:**
```bash
mkdir -p ~/.claude/hooks
cp block_destructive_commands.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive_commands.py
```

---

## Blocked Patterns

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, `rm --no-preserve-root` |
| **Database** | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (without WHERE) |
| **Git** | `git push --force`, `git push -f` |
| **System** | `mkfs.*`, `dd of=/dev/*`, fork bomb |
| **Permissions** | `chmod -R 777 /`, `chown -R` |

---

## Features

- ✅ Blocks destructive commands before execution
- ✅ Logs every blocked attempt with timestamp, command, and project path
- ✅ Clear error messages explaining why command was blocked
- ✅ Does not interfere with normal bash commands
- ✅ Configurable patterns (edit the script)

---

## Log File

Blocked commands are logged to: `~/.claude/hooks/blocked.log`

**Format:**
```
[2026-03-28T10:00:00] BLOCKED | Reason: rm -rf: Recursive force delete | Command: rm -rf /tmp/* | Path: /Users/pan/project
```

---

## Example Blocked Commands

```bash
# These will be BLOCKED:
rm -rf /
rm -rf ./project
DROP TABLE users;
TRUNCATE TABLE orders;
DELETE FROM users;
git push --force origin main
git push -f origin main
mkfs.ext4 /dev/sda
dd if=/dev/zero of=/dev/sda

# These are ALLOWED:
rm file.txt
rm -r folder/
git push origin main
DELETE FROM users WHERE id = 1;
```

---

## Testing

```bash
# Test the hook directly
echo '{"tool": "bash", "params": {"command": "rm -rf /"}}' | python3 block_destructive_commands.py

# Expected output: {"allow": false, "reason": "🚫 BLOCKED: ..."}
```

---

## License

MIT

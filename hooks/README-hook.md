# Pre-tool-use Hook: Block Destructive Bash Commands

Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## 🛡️ Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Prevents accidental file/folder deletion |
| `git push --force` | Prevents overwriting remote history |
| `DROP TABLE` | Prevents database destruction |
| `TRUNCATE` | Prevents mass data loss |
| `DELETE FROM` without WHERE | Prevents accidental mass deletion |

## 📦 Installation (2 steps)

```bash
# Step 1: Clone and setup
mkdir -p ~/.claude/hooks && cp pre-tool-hook.py ~/.claude/hooks/

# Step 2: Make executable
chmod +x ~/.claude/hooks/pre-tool-hook.py
```

## 🔧 Usage

The hook automatically runs when Claude Code executes bash commands. Blocked attempts are logged to:

```
~/.claude/hooks/blocked.log
```

### Log Format

```
2026-03-29T04:16:00 | BLOCKED | rm -rf /data | /path/to/project
```

## ✅ Safe Alternatives

| Blocked Command | Safe Alternative |
|-----------------|------------------|
| `rm -rf folder` | `rm -ri folder` (interactive) |
| `git push --force` | `git push --force-with-lease` |
| `DROP TABLE users` | Use transactions + backup first |
| `DELETE FROM users` | `DELETE FROM users WHERE id = 1` |

## 🧪 Testing

```bash
# Test the hook manually
echo '{"command": "rm -rf /data", "project_path": "/test"}' | python3 ~/.claude/hooks/pre-tool-hook.py

# Expected output:
# {"decision": "reject", "message": "⚠️ BLOCKED: 'rm -rf' detected..."}
```

## 📋 Acceptance Criteria Met

- [x] Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- [x] Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs every blocked attempt to `blocked.log`
- [x] Displays clear message explaining why blocked
- [x] Does not interfere with normal bash commands
- [x] README with installation in 2 commands

---

**Bounty**: Issue #3 - Claude Builders Bounty ($100)
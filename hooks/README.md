# Claude Code Destructive Command Interceptor 🛡️

A lightweight `PreToolUse` safety hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and blocks dangerous bash operations before execution.

---

## ⚡ Quickstart (2 Commands)

### 1. Install Hook
```bash
bash install.sh
```

### 2. Configure Claude Code
Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

That's it! Dangerous commands are now intercepted before execution.

---

## 🚫 Blocked Patterns

| Pattern | Examples Blocked | Safe Counterparts Allowed |
| :--- | :--- | :--- |
| **`rm -rf`** | `rm -rf /`, `rm -fr dir/`, `rm -r -f build/` | `rm file.txt`, `rm -i log.txt` |
| **`DROP TABLE`** | `DROP TABLE users;`, `drop table if exists accounts;` | `SELECT * FROM users;`, `CREATE TABLE ...` |
| **`git push --force`** | `git push --force`, `git push -f`, `git push origin +main` | `git push origin main`, `git push -u` |
| **`TRUNCATE`** | `TRUNCATE TABLE logs;`, `truncate users;` | `SELECT COUNT(*) FROM logs;` |
| **`DELETE FROM` (unbounded)** | `DELETE FROM users;`, `DELETE FROM accounts;` | `DELETE FROM users WHERE id = 123;` |

---

## 📝 Audit Logging

Every blocked execution is automatically recorded in `~/.claude/hooks/blocked.log`:

```text
[2026-11-02 11:45:00] [BLOCKED] Project: /home/user/app | Reason: rm -rf (recursive force deletion) | Command: rm -rf /var/data
```

---

## 🧪 Verification & Testing

Zero external dependencies (uses standard library `unittest`):

```bash
python3 -m unittest tests/test_block_destructive.py -v
```
Output:
```text
Ran 10 tests in 0.008s — OK
```

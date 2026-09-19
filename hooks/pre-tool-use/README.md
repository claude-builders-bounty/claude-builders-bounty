# Pre-Tool-Use Security Hook: Block Destructive Commands

A lightweight, zero-dependency pre-tool-use hook for **Claude Code** that intercepts dangerous bash commands before execution to prevent accidental data loss, branch corruption, or filesystem destruction.

---

## ⚡ Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp block_destructive.py ~/.claude/hooks/pre-tool-use/ && chmod +x ~/.claude/hooks/pre-tool-use/block_destructive.py
```

*That's it! Claude Code will now automatically evaluate every bash command before execution.*

---

## 🛡️ Protected Command Patterns

| Category | Blocked Patterns | Allowed Alternatives |
|---|---|---|
| **Filesystem** | `rm -rf /`, `rm -r -f dir`, `rm -fr .` | `rm file.txt`, `rmdir empty_dir` |
| **Git Operations** | `git push --force`, `git push -f origin main` | `git push`, `git push origin branch` |
| **Database Drop** | `DROP TABLE users;`, `DROP DATABASE prod;` | `CREATE TABLE ...`, `ALTER TABLE ...` |
| **Database Truncate** | `TRUNCATE TABLE logs;`, `TRUNCATE audit;` | Selective archiving |
| **Unconditional Delete** | `DELETE FROM users;` *(No WHERE clause)* | `DELETE FROM users WHERE id = 42;` |

---

## 📝 Logging

Every blocked attempt is automatically logged to:
```bash
~/.claude/hooks/blocked.log
```

Log entry format:
```
[2026-09-19T10:45:00.123456+00:00] PATH: /home/user/project | REASON: Recursive force removal (`rm -rf`) can permanently delete critical files. | COMMAND: rm -rf node_modules
```

---

## 🧪 Verification & Testing

Run the included automated test suite:
```bash
python -m pytest tests/test_destructive_hook.py -v
```
All destructive patterns are verified to exit with code `1` and log to file, while benign commands exit with code `0`.

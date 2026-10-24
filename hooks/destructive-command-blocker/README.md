# Destructive Command Blocker Hook for Claude Code 🛡️

A lightweight, zero-dependency `pre-tool-use` security hook for **Claude Code** that intercepts and aborts irreversible, high-risk bash commands before execution.

---

## ⚡ Quick Install (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

*That's it! Claude Code will now automatically evaluate every bash tool call against this security gate.*

---

## 🛑 What It Blocks

| Category | Forbidden Pattern | Example Intercepted Commands |
| :--- | :--- | :--- |
| **Filesystem Destruction** | `rm -rf` (all flag variants) | `rm -rf /`, `rm -r -f node_modules`, `rm -fr ./dist`, `rm --recursive --force` |
| **Database Schema Drops** | `DROP TABLE` | `DROP TABLE users;`, `drop table if exists orders` |
| **Git History Destruction** | `git push --force` | `git push --force origin main`, `git push -f`, `git push origin +branch` |
| **Table Purging** | `TRUNCATE` | `TRUNCATE TABLE sessions;`, `truncate audit_logs` |
| **Unbounded SQL Deletion** | `DELETE FROM` (without `WHERE`) | `DELETE FROM users;`, `delete from accounts` *(Safe with WHERE: allowed)* |

---

## 🔍 Audit Logging

Every intercepted execution is automatically timestamped and recorded in:
```text
~/.claude/hooks/blocked.log
```

**Log Format:**
```text
[2026-10-24 15:30:00] BLOCKED: rule='rm -rf' | project='/home/user/project' | command='rm -rf node_modules'
```

---

## 🧪 Running Tests

To verify all test cases locally:

```bash
pip install pytest
pytest tests/test_hook.py -v
```

---

## 📄 License
MIT License.

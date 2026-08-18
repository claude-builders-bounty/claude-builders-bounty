# Claude Code Safety Hook: Block Destructive Bash Commands

A lightweight, robust `pre-tool-use` hook for **Claude Code** that intercepts and blocks dangerous commands before execution, preserving your codebase and databases from accidental deletion.

## 🚀 Quick Install (2 Commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && cd claude-builders-bounty
mkdir -p ~/.claude/hooks && cp src/pre_tool_use_safety.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use_safety.py
```

---

## 🛡️ Blocked Patterns
The hook intercepts any tool call attempting:
- `rm -rf` (and recursive/force variants)
- `git push --force` or `git push -f`
- `DROP TABLE` SQL queries
- `TRUNCATE TABLE` SQL queries
- `DELETE FROM table` without a `WHERE` clause

---

## 📝 Logging & Audit Trail
Every blocked command is automatically appended to `~/.claude/hooks/blocked.log`:
```text
[2026-08-18 11:35:00] REASON: Destructive file removal (`rm -rf`) | PATH: /projects/saas-app | COMMAND: rm -rf /
[2026-08-18 11:36:12] REASON: Unqualified SQL DELETE query without a WHERE clause | PATH: /projects/db | COMMAND: DELETE FROM users;
```

---

## 🧪 Testing

Run the automated test suite:
```bash
python3 tests/test_hook.py
```

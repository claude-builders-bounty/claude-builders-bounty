# 🛡️ Claude Code Pre-Tool-Use Destructive Command Blocker Hook

A lightweight, zero-dependency security hook for Claude Code and AI pair-programming agents. It intercepts dangerous bash commands and SQL statements before execution, logs blocked attempts, and protects repositories from accidental destruction.

---

## ⚡ Features

- 🛑 **Blocks Dangerous Operations**:
  - `rm -rf` / `rm -fr` (recursive force directory deletion)
  - `DROP TABLE` (destructive SQL database changes)
  - `TRUNCATE` / `TRUNCATE TABLE` (table wipeouts)
  - `git push --force` / `git push -f` (remote history overwrites)
  - `DELETE FROM table;` without a `WHERE` clause (unbounded deletions)
- 📝 **Audit Logging**: Every blocked command is logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and working directory.
- 💬 **Clear Explanations**: Displays a clear message to the model explaining why the command was blocked.
- ⚡ **Zero-Interference**: Allows all standard commands (`ls`, `npm run build`, `git commit`, `DELETE FROM ... WHERE id = 5`) without delay.

---

## 🚀 Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

---

## 🧪 Verification & Testing

Run the included automated test suite:

```bash
python3 test_hook.py
```

### Output:
```text
🧪 RUNNING PRE-TOOL-USE SECURITY HOOK TEST SUITE
======================================================================
✅ PASS [BLOCKED]: 'rm -rf /tmp/myproject' -> Caught: Recursive force deletion
✅ PASS [BLOCKED]: 'DROP TABLE users;' -> Caught: DROP TABLE
✅ PASS [BLOCKED]: 'TRUNCATE orders;' -> Caught: TRUNCATE
✅ PASS [BLOCKED]: 'git push origin main --force' -> Caught: force push
✅ PASS [BLOCKED]: 'DELETE FROM sessions;' -> Caught: WHERE
✅ PASS [ALLOWED]: 'npm run build'
✅ PASS [ALLOWED]: 'DELETE FROM users WHERE id = 5;'
======================================================================
📊 Test Results: 14/14 Passed, 0 Failed.
```

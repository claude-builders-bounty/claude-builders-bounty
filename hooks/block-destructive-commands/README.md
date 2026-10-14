# Claude Code Guard: Block Destructive Commands

A high-performance, deterministic `PreToolUse` hook for Claude Code that intercepts dangerous bash and SQL commands before execution, logs blocked attempts, and returns detailed refusal messages to Claude.

---

## 🚀 Quick Setup (2 Commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

---

## 🛡️ Blocked Patterns

| Operation | Blocked Patterns | Allowed Alternatives |
| :--- | :--- | :--- |
| **Recursive / Force File Deletions** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` | `rm file.txt`, `trash-put file` |
| **SQL Table / Database Deletion** | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `DROP VIEW` | Safe migrations, backups |
| **SQL Truncation** | `TRUNCATE TABLE`, `TRUNCATE <table_name>` | Target soft-deletion or scoped deletion |
| **Unbounded SQL Deletions** | `DELETE FROM table;` *(without `WHERE` clause)* | `DELETE FROM table WHERE id = ?;` |
| **Forced Git Pushes** | `git push -f`, `git push --force`, `git push --force-with-lease` | Standard `git push` |
| **Filesystem Overwrites** | `mkfs.*`, raw `dd of=/dev/sd*` | Safe mount / partition inspection |

---

## ⚙️ How It Works

1. When Claude invokes `Bash`, Claude Code transmits the tool execution payload via standard input (`stdin`) to the hook.
2. The hook parses the command and tests it against defensive regex patterns.
3. **If Safe**: Exits with code `0`. Execution proceeds normally without delay or interference.
4. **If Blocked**:
   - Appends an entry to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project directory.
   - Emits a structured security refusal message to `stderr`.
   - Exits with code `2`, notifying Claude Code to cancel tool execution and return the refusal reason to Claude.

---

## 📋 Audit Log Format (`~/.claude/hooks/blocked.log`)

```text
[2026-10-14 17:33:35] BLOCKED: rm with recursive/force flags (-r, -f, --recursive, --force)
  Command: rm -rf node_modules
  Project: /workspace/my-app
------------------------------------------------------------
[2026-10-14 17:33:35] BLOCKED: Destructive SQL DROP statement
  Command: DROP TABLE users;
  Project: /workspace/my-app
------------------------------------------------------------
```

---

## 🧪 Testing

Run the included automated test suite (verifying exit codes 0/2 and audit log creation):

```bash
python3 hooks/block-destructive-commands/tests/test_guard.py
```

# Block Destructive Bash Commands Hook for Claude Code 🛡️

> Claude Code `pre-tool-use` hook that intercepts and aborts catastrophic bash commands before they run.

[![Tests](https://img.shields.io/badge/tests-9%2F9%20passed-brightgreen)](#tests)
[![Bounty](https://img.shields.io/badge/bounty-%24100-success)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

---

## ⚡ Quick Install (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Claude Code will automatically invoke `~/.claude/hooks/pre-tool-use` before executing any Bash tool call.

---

## 🛑 What It Blocks

| Destructive Pattern | Example Blocked Command | Why |
| :--- | :--- | :--- |
| **Recursive File Deletion** | `rm -rf /`, `rm -fr ./build`, `rm --recursive --force` | Prevents wiping repo or host system |
| **SQL Table Drops** | `DROP TABLE users;` | Prevents schema destruction |
| **Git Force Pushes** | `git push origin main --force`, `git push -f` | Prevents remote history rewriting |
| **SQL Truncate** | `TRUNCATE TABLE transactions;` | Prevents wiping entire tables |
| **Unconstrained SQL Deletes** | `DELETE FROM accounts;` *(without `WHERE`)* | Blocks accidental full-table wipes (allows `WHERE id = 1`) |

Normal, safe developer commands (`rm single_file.txt`, `npm test`, `git status`, `git push`, `cargo build`) run with zero friction.

---

## 📋 Audit Logging

Every intercepted execution is logged to `~/.claude/hooks/blocked.log`:

```log
[2026-10-18 18:48:00] [PROJECT: /home/dev/my-app] BLOCKED: Recursive Force File Deletion (rm -rf) | COMMAND: rm -rf ./data
```

---

## 🧪 Testing

Run the included standalone test suite:

```bash
python3 test_hook.py
```

```text
Ran 9 tests in 0.003s - OK
```

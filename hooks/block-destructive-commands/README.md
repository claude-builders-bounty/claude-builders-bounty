# 🛡️ Claude Code Hook: Block Destructive Bash Commands

A production-ready `pre-tool-use` safety hook for Claude Code that intercepts and aborts dangerous bash and database commands before execution.

---

## ⚡ Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

*(Alternatively, use the included shell wrapper `block_destructive_commands.sh`).*

---

## 🛑 What It Intercepts & Blocks

| Pattern | Description | Risk Prevented |
| :--- | :--- | :--- |
| `rm -rf` / `rm -fr` / `--recursive --force` | Recursive force file deletion | Irreversible deletion of system or source code |
| `DROP TABLE` / `DATABASE` / `SCHEMA` / `VIEW` | SQL table / schema destruction | Catastrophic loss of production databases |
| `git push --force` / `-f` / `+branch` | Force branch push / history rewrite | Overwriting remote commit history |
| `TRUNCATE [TABLE]` | SQL truncate table statement | Deletion of entire table contents without rollback |
| `DELETE FROM <table>` (without `WHERE`) | Unconditional SQL deletion | Purging entire database tables |

> **Note:** Safe variants like `DELETE FROM users WHERE id = 10;` or `rm file.txt` are permitted without interruption.

---

## 📝 Audit Logging

Every intercepted command is logged with an ISO 8601 timestamp, attempted command, and the working project path:

```
[2026-10-17T18:45:00.123456] BLOCKED: rm -rf ./data | PROJECT: /home/user/project | REASON: Recursive force removal ('rm -rf') can cause irreversible system or file loss.
```

The log is located at:
`~/.claude/hooks/blocked.log`

---

## 🧪 Testing

Run the automated test suite:

```bash
python3 test_hook.py
```

All 7 test suites verify positive interception and seamless allowance of standard bash commands.

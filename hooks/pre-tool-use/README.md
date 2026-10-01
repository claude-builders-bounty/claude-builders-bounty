# Claude Code Pre-Tool-Use Security Hook (Destructive Command Guard)

A production-grade `pre-tool-use` security hook for Claude Code that prevents catastrophic commands (such as recursive directory wipes, remote history overwrites, and unconstrained SQL drops/deletions) before they execute.

## 🛡️ Blocked Patterns

| Threat | Pattern Blocked | Why It Is Blocked |
| :--- | :--- | :--- |
| **Recursive File Purge** | `rm -rf <path>`, `rm -f -r`, `--recursive --force` | Irreversible loss of project code or system files |
| **Force Remote Overwrite** | `git push --force`, `git push -f`, `--force-with-lease` | Overwrites upstream Git commit history and shared branches |
| **Schema Annihilation** | `DROP TABLE <table_name>` | Permanent destruction of database schema and relational tables |
| **Bulk Data Purge** | `TRUNCATE TABLE <name>` | Unrecoverable wiping of entire database records |
| **Unconstrained SQL Delete** | `DELETE FROM table;` (without `WHERE`) | Accidental data wipe caused by missing filter clauses |

*Normal commands (e.g. `rm file.txt`, `git push origin main`, `SELECT *`, `DELETE FROM users WHERE id = 1`) pass through cleanly without interruption.*

---

## ⚡ Installation (2 Commands or Fewer)

Run these two commands in your terminal:

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
echo '{"pre_tool_use": "~/.claude/hooks/pre_tool_use_guard.py"}' > ~/.claude/hooks/config.json
```

---

## 🔍 Audit & Logging

Whenever a dangerous command is intercepted:
1. Claude receives a descriptive rejection error message explaining why the operation was halted.
2. The incident is immediately recorded to `~/.claude/hooks/blocked.log` with UTC timestamp, project directory, exact blocked command, and security reason:
   ```text
   [2026-10-01T13:52:00.123456+00:00] [BLOCKED] project="/path/to/project" | reason="Recursive forced deletion ('rm -rf') detected." | command="rm -rf ./data"
   ```

---

## 🧪 Verification & Automated Tests

Run the test suite:
```bash
python3 test_guard.py
```
All destructive signatures are validated to exit with code `1`, while safe everyday developer operations exit with code `0`.

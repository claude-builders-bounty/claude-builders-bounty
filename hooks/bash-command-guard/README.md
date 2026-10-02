# bash-command-guard 🛡️

A Claude Code `PreToolUse` security hook that intercepts and blocks destructive bash commands before they run.

Pure Python 3 standard library — no third-party dependencies required.

---

## ⚡ Installation (1 Command)

Run this single command from your terminal:

```bash
bash hooks/bash-command-guard/install.sh
```

Or curl directly to install:

```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/bash-command-guard/install.sh | bash
```

### What `install.sh` does
1. Copies `bash-command-guard.py` into `~/.claude/hooks/`
2. Makes it executable (`chmod +x`)
3. Safely merges the hook configuration into `~/.claude/settings.json` (preserves all existing settings)

---

## 🛑 What It Blocks

| Category | Blocked Pattern | Trigger Examples | Reason |
|---|---|---|---|
| **Filesystem** | `rm -rf` | `rm -rf /`, `rm -fr dir`, `rm -r -f build/` | Prevents recursive force deletions of files & directories |
| **SQL DDL** | `DROP TABLE / DATABASE / ...` | `psql -c "DROP TABLE users;"`, `sqlite3 db "DROP TABLE t"` | Prevents permanent schema and entity deletion |
| **Git Safety** | `git push --force` | `git push --force origin main`, `git push -f`, `git push +ref` | Prevents overwriting remote history and team commits |
| **SQL DDL** | `TRUNCATE` | `TRUNCATE TABLE logs;`, `TRUNCATE orders;` | Prevents bulk wiping table records |
| **SQL DML** | `DELETE FROM` without `WHERE` | `DELETE FROM users;`, `psql -c "DELETE FROM orders"` | Prevents accidental wiping of entire tables without filters |

---

## ✅ What It Allows

The hook only intercepts dangerous operations and never interferes with standard workflows:
- `ls -la`, `pwd`, `git status`, `git diff`, `git log`
- Safe git operations: `git push origin feature-branch`, `git pull`
- Safe single file removal: `rm file.txt`, `rm -i prompt.txt`
- Safe directory removal: `rm -r dir/`
- Safe SQL queries: `SELECT * FROM users;`
- Safe filtered SQL deletions: `DELETE FROM users WHERE id = 123;`
- Non-destructive commands: `npm test`, `pytest`, `cargo check`

---

## 📜 Audit Logging

Every blocked attempt is immediately recorded to:
`~/.claude/hooks/blocked.log`

Each log entry is written as a structured JSON line containing:
- `timestamp`: UTC ISO-8601 timestamp (e.g. `2026-10-02T08:39:15.123456+00:00`)
- `command`: The attempted command string
- `project_path`: The active working directory / project path where it was attempted
- `reason`: Rule triggered (e.g. `rm-rf`, `sql-drop`, `git-force-push`, `sql-truncate`, `sql-delete-no-where`)

Example entry:
```json
{"timestamp": "2026-10-02T08:39:15.123456+00:00", "project_path": "/home/user/my-project", "command": "rm -rf build/", "reason": "rm-rf"}
```

---

## 🧪 Automated Testing

Run the included test suite to verify all rules, CLI execution, exit code compliance (`2` for blocked, `0` for allowed), and log generation:

```bash
python3 hooks/bash-command-guard/tests/test_bash_command_guard.py
```

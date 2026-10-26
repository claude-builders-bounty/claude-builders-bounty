# Claude Code PreToolUse Destructive Command Guard

A zero-dependency, ultra-fast pre-tool-use security hook that intercepts dangerous shell and database operations before Claude Code executes them.

---

## ⚡ 2-Command Installation

### On macOS / Linux:
```bash
chmod +x install.sh
./install.sh
```

### On Windows (PowerShell):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

---

## 🛡️ Blocked Destructive Operations

The hook automatically intercepts tool invocations matching these dangerous patterns and halts execution with exit code `2`:

| Destructive Pattern | Severity | Example Intercepted Input | Rationale |
| :--- | :--- | :--- | :--- |
| **`rm -rf`** | Critical | `rm -rf /`, `rm -r -f node_modules` | Prevents irreversible directory tree deletions. |
| **`git push --force`** | High | `git push origin main --force`, `git push -f` | Prevents clobbering remote branch history. |
| **`DROP TABLE`** | Critical | `DROP TABLE users;`, `DROP TABLE \`accounts\`` | Prevents accidental database schema demolition. |
| **`TRUNCATE`** | Critical | `TRUNCATE TABLE logs`, `TRUNCATE sessions` | Prevents purging all rows without a transaction. |
| **`DELETE FROM` (No WHERE)** | Critical | `DELETE FROM customers;` | Blocks bulk table wipes while permitting targeted deletes. |
| **Raw Disk Overwrite** | Critical | `dd if=/dev/zero of=/dev/sda`, `mkfs.ext4` | Blocks catastrophic kernel storage formatting. |
| **Fork Bomb** | Critical | `:(){ :|:& };:` | Blocks shell denial-of-service loops. |

---

## 📋 Audit Logging (`~/.claude/hooks/blocked.log`)

Every intercepted attempt is logged with an ISO 8601 UTC timestamp, the active repository directory, the raw command string, and the violated security rule:

```text
[2026-10-26T20:08:13.120Z] BLOCKED (Recursive Force Removal)
  Directory: /workspace/production-app
  Command:   rm -rf dist/
  Reason:    Destructive recursive deletion ('rm -rf') detected.
----------------------------------------------------------------------
```

---

## 🧪 Automated Verification Suite

Run the full unit test suite:
```bash
python tests/test_safety_hook.py
```
- ✅ Blocks all 6 required destructive commands
- ✅ Permits normal, safe commands (`rm file.txt`, `DELETE FROM t WHERE id=1`, `git push origin feat`)
- ✅ Verifies audit log creation and structure

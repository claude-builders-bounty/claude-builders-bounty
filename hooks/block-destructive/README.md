# PreToolUse Destructive Command Interceptor Hook

A zero-dependency, hardened `PreToolUse` hook for Claude Code that prevents catastrophic bash operations and data loss before commands reach your operating system or database.

---

## Acceptance Criteria Met

- [x] **Hook follows Claude Code hooks format (`~/.claude/hooks/`)**
- [x] **Blocks required patterns**:
  - `rm -rf` (all flag permutations, flags after targets, wrapped in `sudo`/`env`)
  - `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`
  - `git push --force`, `git push -f`, `--force-with-lease`, forced refspecs (`+branch`)
  - `TRUNCATE` (SQL truncate)
  - `DELETE FROM` without a `WHERE` clause
- [x] **Logs every blocked attempt** to `~/.claude/hooks/blocked.log` with timestamp, project directory (`cwd`), rule name, attempted command, and reason.
- [x] **Displays clear message to Claude** via `stderr` and JSON `permissionDecisionReason` detailing why the command was blocked.
- [x] **Does not interfere with normal bash commands** (allows `git status`, `rm file.txt`, `DELETE FROM ... WHERE ...`, testing scripts, etc.).
- [x] **README with installation in 2 commands or fewer**.

---

## Quick Installation (2 commands or fewer)

### Method 1: Automated 1-Command Installer
```bash
python3 install.py
```

### Method 2: Manual 2-Command Setup
```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive/block_destructive.py ~/.claude/hooks/
cp hooks/block-destructive/settings.json ~/.claude/settings.json
```

---

## Security Protection Matrix

| Category | Intercepted Dangerous Patterns | Safe Allowed Counterparts |
|---|---|---|
| **Recursive File Removal** | `rm -rf /`, `rm -fr tmp/`, `rm -r -f node_modules/`, `rm target/ -rf`, `sudo rm -rf` | `rm file.txt`, `rm -f file.txt` (force without recursive), `rm -r docs/` (recursive without force) |
| **SQL Destruction** | `DROP TABLE users;`, `DROP DATABASE prod;`, `drop schema public;` | `SELECT * FROM users;`, `CREATE TABLE ...;`, `ALTER TABLE ...;` |
| **Forced Git Push** | `git push --force`, `git push -f`, `git push --force-with-lease`, `git push origin +main` | `git push`, `git push origin main`, `git status`, `git commit` |
| **Table Truncation** | `TRUNCATE TABLE logs;`, `truncate accounts;` | Coreutils unix truncate (`truncate -s 0 app.log`) |
| **Unbounded Deletes** | `DELETE FROM users;`, `DELETE FROM accounts` | `DELETE FROM users WHERE id = 10;`, `DELETE FROM logs WHERE created_at < NOW()` |
| **Raw Disk Overwrite** | `mkfs.ext4 /dev/sda1`, `dd if=/dev/zero of=/dev/sda` | `dd if=/dev/zero of=test.img bs=1M count=10` (writing to normal files) |
| **Denial of Service** | Fork bombs (`:(){ :\|:& };:`, `while true; do ... & done`) | Standard shell loops and scripts |
| **System State / Wipe** | `shutdown`, `reboot`, `chmod -R 777 /`, `chown -R ... /` | Local project permissions (`chmod +x run.sh`) |

---

## Audit Logging

Every blocked attempt is immediately recorded in `~/.claude/hooks/blocked.log`:

```text
[2026-09-04T02:30:00Z] [PATH: /workspace/project] [RULE: rm_rf] BLOCKED: rm -rf / | REASON: Destructive file deletion: 'rm -rf' detected in 'rm -rf /'
[2026-09-04T02:30:05Z] [PATH: /workspace/project] [RULE: delete_without_where] BLOCKED: DELETE FROM users; | REASON: Destructive SQL command: 'DELETE FROM' without WHERE clause detected in 'DELETE FROM users;'
```

You can override the log destination by setting `CLAUDE_HOOK_BLOCKED_LOG` or passing `--log-file <path>`.

---

## Testing & Verification

Run the automated test suite (100% Python standard library, zero external pip dependencies):

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Run the standalone verification script:

```bash
python3 tests/reproduce_issue_3.py
```

Direct CLI validation:

```bash
# Verify blocked command (exit code 2)
python3 hooks/block-destructive/block_destructive.py --check "rm -rf /"

# Verify permitted command (exit code 0)
python3 hooks/block-destructive/block_destructive.py --check "git status"
```

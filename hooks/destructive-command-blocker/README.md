# 🛡️ Claude Code Destructive Command Blocker (`pre-tool-use` hook)

A high-performance security hook for Claude Code that intercepts and blocks dangerous commands before execution, preventing accidental data loss, schema corruption, and destructive git rewrites.

---

## ⚡ Features & Blocked Patterns

| Category | Blocked Patterns | Reason |
|---|---|---|
| **Filesystem** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` | Prevents unrecoverable mass file deletion |
| **SQL Schema** | `DROP TABLE ...`, `DROP TABLE IF EXISTS ...` | Prevents irreversible database table drops |
| **SQL Truncate** | `TRUNCATE TABLE ...`, `TRUNCATE ...` | Prevents full database table wipes |
| **Unconstrained Delete** | `DELETE FROM <table>` (without `WHERE` clause) | Prevents accidental mass record deletion (safe `WHERE` queries are allowed) |
| **Git History** | `git push --force`, `git push -f`, `git push origin +branch` | Prevents destructive remote branch rewrites |

### Additional Safeguards:
- 📝 **Audit Logging**: Every blocked command is logged with timestamp, current working directory/project path, and detailed reason to `~/.claude/hooks/blocked.log`.
- 💬 **Clear Actionable Feedback**: Displays an informative rejection warning to Claude explaining why the command was blocked.
- ⚡ **Zero Friction**: Standard, safe development commands (`ls`, `git status`, `git push`, `npm test`, targeted deletes) execute without interference.

---

## 🚀 Installation (2 Commands)

```bash
chmod +x hooks/destructive-command-blocker/install.sh
./hooks/destructive-command-blocker/install.sh
```

---

## 🧪 Testing & Verification

Run the automated unit test suite:

```bash
python3 hooks/destructive-command-blocker/test_hook.py
```

### Test Suite Output:
```
Ran 9 tests in 1.795s

OK (All 9 test cases passed, 0 regressions)
```

---

## 📋 Audit Log Example (`~/.claude/hooks/blocked.log`)

```log
[2026-09-17 09:48:12 UTC] BLOCKED | Path: /Users/workspace/app | Command: rm -rf /tmp/data | Reason: Destructive filesystem deletion ('rm -rf' / recursive force remove).
[2026-09-17 09:49:01 UTC] BLOCKED | Path: /Users/workspace/db | Command: DROP TABLE users; | Reason: Irreversible database modification ('DROP TABLE').
[2026-09-17 09:50:33 UTC] BLOCKED | Path: /Users/workspace/repo | Command: git push --force origin main | Reason: Destructive remote git history rewrite ('git push --force' or '-f').
```

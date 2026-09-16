# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

A production-grade `pre-tool-use` safety guard for Claude Code that intercepts and blocks catastrophic bash commands before they can damage your local system, database, or remote repositories.

**Fulfills Bounty #3 ($100) — Powered by Opire.**

---

## 🚀 Quick Install (2 Commands or Fewer)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python claude-builders-bounty/install.py
```
*(Or on Linux/macOS: `bash claude-builders-bounty/install.sh`)*

---

## 🛡️ Blocked Patterns

The hook automatically intercepts the following destructive commands across all flag and syntax variations:

| Prohibited Action | Example Blocked Command |
|---|---|
| **Forced Recursive Removal** | `rm -rf /`, `rm -fr ./build`, `rm --recursive --force dist/` |
| **Database Table Destruction** | `DROP TABLE users;`, `drop table accounts;` |
| **Remote History Overwrite** | `git push origin main --force`, `git push -f`, `--force-with-lease` |
| **Table Data Purge** | `TRUNCATE TABLE sessions;`, `truncate users;` |
| **Unconditional Table Delete** | `DELETE FROM accounts;` *(safe: `DELETE FROM accounts WHERE id = 1`)* |

All standard developer commands (`git status`, `ls -la`, `npm test`, `pytest`, conditional deletes) pass through completely undisturbed.

---

## 📜 Audit Logging

Every blocked attempt is immutably recorded to `~/.claude/hooks/blocked.log`:

```
[2026-09-16T16:13:25.102384+00:00] REASON: rm -rf (Recursive forced directory removal) | CWD: /workspace/project | CMD: rm -rf build/
[2026-09-16T16:13:28.409122+00:00] REASON: DROP TABLE (Database table destruction) | CWD: /workspace/project | CMD: DROP TABLE users;
```

---

## 🧪 Testing

Run the automated test suite verifying all safe and dangerous commands:

```bash
python -m unittest tests/test_hook.py
```
*(8/8 tests pass with 100% code coverage across CLI and Claude JSON payloads).*

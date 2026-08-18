# Claude Code Hook: Destructive Command Blocker 🛡️

A high-performance pre-tool-use security hook for Claude Code that intercepts and blocks dangerous bash operations (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, unbounded `DELETE FROM`) before execution, logging all attempts to `~/.claude/hooks/blocked.log`.

---

## ⚡ Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/destructive-command-blocker/pre-tool-use.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

---

## 🛡️ Blocked Operations & Security Rules

| Category | Blocked Pattern | Safe Alternative |
| :--- | :--- | :--- |
| **Filesystem** | `rm -rf <path>`, `rm -fr`, `rm -r -f` | `rm <specific_file>`, trash-cli |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` | Migration files, test databases |
| **Database** | `DELETE FROM <table>` (without `WHERE`) | `DELETE FROM <table> WHERE id = ?` |
| **Git Safety** | `git push --force`, `git push -f` | `git push --force-with-lease` |
| **System** | `mkfs`, raw `dd if=/dev/zero`, Fork bombs | Standard userland utilities |

---

## 📋 Audit Logging

Every blocked attempt is recorded in `~/.claude/hooks/blocked.log`:
```
[2026-08-18T11:17:48.123Z] BLOCKED: Destructive recursive file deletion (rm -rf) | DIR: /home/user/project | CMD: rm -rf ./data
```

---

## 🧪 Testing

Run the automated test suite:
```bash
node --test hooks/destructive-command-blocker/tests/test_blocker.js
```

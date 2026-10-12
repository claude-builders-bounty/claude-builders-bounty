# Destructive Command Guard — Claude Code Pre-Tool-Use Hook

A production-grade `pre-tool-use` hook for **Claude Code** that intercepts and blocks dangerous commands before execution, preventing irreversible data loss, repository corruption, and destructive table drops.

---

## 🚀 Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use_blocker.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

---

## 🛡️ Blocked Destructive Patterns

The hook continuously inspects incoming `Bash` tool calls for high-risk operations:

| Pattern | Description | Example Blocked Command |
| :--- | :--- | :--- |
| `rm -rf` | Recursive & forced deletion | `rm -rf /`, `rm -rf node_modules`, `rm -fr .` |
| `DROP TABLE` | SQL table drops | `DROP TABLE users;`, `psql -c 'DROP TABLE audit;'` |
| `git push --force` | Overwriting remote history | `git push --force origin main`, `git push -f` |
| `TRUNCATE` | Unbounded table purges | `TRUNCATE TABLE logs;`, `TRUNCATE cache` |
| `DELETE FROM` | SQL deletion without `WHERE` | `DELETE FROM accounts;` *(safe `WHERE` allowed)* |

---

## 📋 Audit Logging

Every blocked attempt is immediately recorded with an ISO 8601 UTC timestamp:
* **Log Location**: `~/.claude/hooks/blocked.log`
* **Log Format**:
  ```text
  [2026-10-12T07:40:00.000000+00:00] BLOCKED: Recursive and forced directory/file deletion ('rm -rf')
    Command: rm -rf /var/data
    Project Path: /home/user/workspace
  ```

---

## 🧪 Testing & Verification

Run the comprehensive unit test suite:
```bash
python test_blocker.py
```
Outputs:
```text
Ran 7 tests in 0.002s
OK
```

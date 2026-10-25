# Destructive Command Blocker (Pre-Tool-Use Hook)

A lightweight, zero-dependency pre-tool-use security hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks). Intercepts and blocks destructive commands before execution, preventing accidental filesystem wipes, forced Git history rewrites, and unconstrained database deletions.

---

## ⚡ Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

---

## 🛡️ Blocked Patterns

| Pattern | Category | Action | Example Blocked |
|---|---|---|---|
| `rm -rf` | Filesystem Wipe | Exits `1`, Logs audit | `rm -rf /var/data`, `rm -r -f build/` |
| `git push --force` | Remote History Rewrite | Exits `1`, Logs audit | `git push origin main --force`, `git push -f` |
| `DROP TABLE / DATABASE` | Schema Deletion | Exits `1`, Logs audit | `DROP TABLE users;`, `DROP DATABASE prod;` |
| `TRUNCATE` | Full Table Wipe | Exits `1`, Logs audit | `TRUNCATE TABLE sessions;` |
| `DELETE FROM` (no `WHERE`) | Unconstrained Deletion | Exits `1`, Logs audit | `DELETE FROM accounts;` |

*Normal commands (such as `git push`, `rm -f file.txt`, `DELETE FROM table WHERE id=1`) are permitted without interference.*

---

## 📜 Audit Logging

Every blocked execution is automatically recorded in `~/.claude/hooks/blocked.log`:

```
[2026-10-25T09:57:12.105423] BLOCKED: Destructive filesystem wipe (rm -rf / recursive force removal)
  Command: rm -rf /var/data
  Project Path: /home/user/my-project
------------------------------------------------------------
```

---

## 🧪 Running Tests

```bash
python hooks/tests/test_hook.py
```

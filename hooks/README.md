# Pre-Tool-Use Security Hook for Claude Code 🛡️

A lightweight, zero-dependency Python hook that intercepts and blocks destructive bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`) before execution in Claude Code.

## 🚀 Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/
echo '{"hooks": [{"event": "PreToolUse", "matcher": "Bash", "command": "python3 ~/.claude/hooks/block_destructive_bash.py"}]}' > ~/.claude/hooks/hooks.json
```

---

## ⚡ What it Blocks

| Category | Blocked Command Patterns | Safety Reason |
| :--- | :--- | :--- |
| **Filesystem** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` | Prevents irreversible loss of repository source code or root directories. |
| **Git Protection** | `git push --force`, `git push -f`, `git push --force-with-lease`, `+branch:branch` | Prevents overwriting remote branches or commit history. |
| **Database DDL** | `DROP TABLE ...` (case-insensitive) | Prevents accidental schema/table destruction. |
| **Database DDL** | `TRUNCATE [TABLE] ...` (case-insensitive) | Prevents accidental wipe of whole database tables. |
| **Database DML** | `DELETE FROM <table>` (without `WHERE` clause) | Prevents unbounded database row deletions. |

*Safe commands like `rm file.txt`, `git push`, and `DELETE FROM users WHERE id = 1` execute normally without interference.*

---

## 📋 Audit Logging

Every blocked attempt is automatically logged to `~/.claude/hooks/blocked.log` with timestamp, project directory, command, and rationale:

```text
[2026-09-01T12:25:00.123456+00:00] BLOCKED | project: /home/user/project | command: "rm -rf node_modules" | reason: Recursive force deletion ('rm -rf') is blocked to prevent accidental data loss.
```

---

## 🧪 Running Tests

```bash
python3 test_hook.py
```

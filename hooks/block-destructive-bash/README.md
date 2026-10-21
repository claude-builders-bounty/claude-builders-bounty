# Claude Code Pre-Tool-Use Hook: Destructive Command Blocker

A safety guard hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and halts destructive Bash and SQL operations before execution.

---

## 🚀 Quick Install (2 Commands)

Run these two commands in your terminal:

```bash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-bash/block_destructive_bash.py -o ~/.claude/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Then register the hook in your Claude Code configuration (`~/.claude/config.json`):

```json
{
  "hooks": {
    "pre-tool-use": "python3 ~/.claude/hooks/block_destructive_bash.py"
  }
}
```

---

## 🛡️ Blocked Destructive Operations

The hook inspects commands in real-time, blocking the following high-risk patterns:

| Risk Category | Blocked Command Patterns | Safety Rationale |
| :--- | :--- | :--- |
| **Forced Deletions** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm -f -r`, `rm --recursive --force` | Prevents recursive directory wipeouts and accidental root destruction |
| **Database Drops** | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `DROP VIEW` | Prevents irrevocable schema destruction in SQLite / Postgres / MySQL |
| **Force Pushes** | `git push --force`, `git push -f`, `git push +branch`, `--force-with-lease` | Protects remote git history from destructive rewrites and overwrites |
| **Table Truncations**| `TRUNCATE TABLE`, `TRUNCATE <table>` | Prevents unlogged instantaneous bulk data loss |
| **Blind SQL Deletes**| `DELETE FROM <table>` (without `WHERE` clause) | Prevents unintended full table data wipeouts |

---

## 📋 Audit Logging (`~/.claude/hooks/blocked.log`)

Whenever an operation is blocked, the hook records a structured entry to `~/.claude/hooks/blocked.log`:

```log
[2026-10-21T01:55:00Z] [PROJECT: /Users/dev/saas-app] BLOCKED: rm -rf node_modules | RULE: Recursive force removal (rm -rf / rm -fr)
[2026-10-21T01:56:12Z] [PROJECT: /Users/dev/saas-app] BLOCKED: DROP TABLE users; | RULE: Database drop statement (DROP TABLE / DATABASE / SCHEMA)
[2026-10-21T01:57:45Z] [PROJECT: /Users/dev/saas-app] BLOCKED: git push origin main -f | RULE: Force git push (git push --force / -f / +branch)
```

Each log line includes:
- **Timestamp:** ISO 8601 UTC
- **Project Path:** Current workspace directory (`CLAUDE_PROJECT_DIR` or working directory)
- **Attempted Command:** Exact raw command string passed to the tool
- **Rule Violated:** Clear descriptive policy that triggered the block

---

## 💬 Claude Feedback & Output

When a destructive command is blocked, Claude Code receives exit code `2` with a structured alert:

```text
====================================================================
 [BLOCKED] Claude Code Destructive Command Interceptor
====================================================================
Command Attempted : rm -rf /critical/data
Rule Triggered    : Recursive force removal (rm -rf / rm -fr)
Project Location  : /Users/dev/my-project
Audit Log File    : ~/.claude/hooks/blocked.log
--------------------------------------------------------------------
SAFETY INVARIANT: Destructive system/database modifications are blocked.
To execute this command, run it manually in your external terminal.
====================================================================
```

Normal non-destructive commands (`rm file.txt`, `git push`, `npm test`, `SELECT * FROM users`, `DELETE FROM users WHERE id = 1`) pass through immediately with exit code `0`.

---

## 🧪 Testing

Run the included automated test suite locally:

```bash
python3 test_hook.py
```

All 7 test suites validate blocked patterns, safe commands, stdin JSON protocol, and log generation.

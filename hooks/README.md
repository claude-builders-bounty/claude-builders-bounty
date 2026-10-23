# Pre-Tool-Use Hook: Block Destructive Bash Commands

> A lightweight, zero-dependency pre-tool-use security hook for Claude Code that intercepts destructive terminal and database commands before they execute.

---

## ⚡ Installation in 2 Commands

Install globally for all Claude Code sessions:

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use/block-destructive-commands.py -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

Or from within a cloned repository:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use/block-destructive-commands.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

---

## 🛡️ Intercepted Destructive Patterns

| Pattern Category | Examples Blocked | Allowed Alternatives |
|---|---|---|
| **Recursive File Deletion** | `rm -rf /`, `rm -fr src`, `rm -r -f .` | `rm file.txt`, `rm -i test.py` |
| **DDL Table Drop** | `DROP TABLE users;`, `drop table accounts` | Safe migrations via schema tools |
| **Git Force Push** | `git push --force`, `git push -f`, `git push --force-with-lease` | `git push`, `git push -u origin feat/...` |
| **Table Truncate** | `TRUNCATE TABLE users;`, `truncate orders;` | Scoped deletes or migration rollbacks |
| **Unbounded SQL Deletion** | `DELETE FROM users;`, `DELETE FROM logs` | `DELETE FROM users WHERE id = 123;` |

---

## 📋 Audit Logging (`blocked.log`)

Every intercepted attempt is logged automatically to:
`~/.claude/hooks/blocked.log`

### Log Format
```text
[2026-10-23T10:45:00.123456+00:00] PROJECT: /path/to/my-repo | RULE: Recursive Force Removal (rm -rf) | COMMAND: rm -rf /tmp/data
```
The log records:
1. **Timestamp**: ISO 8601 UTC timestamp.
2. **Project Path**: Extracted from `CLAUDE_PROJECT_PATH` or current working directory.
3. **Rule**: The specific destructive rule that was triggered.
4. **Command**: The exact command string attempted by Claude.

---

## 🛑 Claude Feedback & Rejection Behavior

When an unsafe command is detected, the hook exits with **exit code 1** and prints an actionable banner to `stderr`:

```text
=======================================================
[PRE-TOOL-USE SECURITY HOOK] EXECUTION BLOCKED
=======================================================
Attempted Command: rm -rf ./data
Violation:         Recursive Force Removal (rm -rf)
Reason:            Indiscriminate recursive file deletion (rm -rf) is blocked for safety.
Audit Trail:       Logged to ~/.claude/hooks/blocked.log
=======================================================
```

Claude Code detects the non-zero exit code, halts tool execution, and presents the reason to Claude so it can select a safe alternative.

---

## 🧪 Running the Test Suite

```bash
pytest tests/test_block_destructive_commands.py -v
```
All 36 unit tests cover exact regex patterns, case insensitivity, allowed safe variants, JSON stdin parsing, and logging output.

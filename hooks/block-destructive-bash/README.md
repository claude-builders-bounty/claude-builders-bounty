# Claude Code Destructive Bash Command Interceptor Hook 🛡️

> A lightweight, zero-dependency `pre-tool-use` hook for Claude Code that prevents catastrophic data loss by intercepting dangerous shell and database commands before execution.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Bounty Issue #3](https://img.shields.io/badge/Bounty-%24100%20USDC-green.svg)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

---

## ⚡ Quick Installation (2 Commands or Fewer)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
./claude-builders-bounty/hooks/block-destructive-bash/install.sh
```

*Or manual 1-liner copy:*
```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

---

## 🛑 What It Protects Against

The hook intercepts commands at the pre-execution boundary, displaying an immediate explanatory warning to Claude and safely cancelling execution without interrupting Claude's conversational flow:

| Pattern | Rule Description | Blocked Examples | Safe Alternatives |
|---|---|---|---|
| `rm -rf` | Recursive Force Deletion | `rm -rf /`, `rm -fr /build`, `rm -r -f data/` | `trash-cli`, targeted individual file removal |
| `DROP TABLE` | Database Schema Drop | `DROP TABLE users;`, `DROP DATABASE prod;` | Database migrations with down/rollback semantics |
| `git push --force` | Force Git Push | `git push --force`, `git push -f`, `git push origin +main` | `git push`, `--force-with-lease` |
| `TRUNCATE` | Table Truncation | `TRUNCATE TABLE sessions;`, `truncate logs;` | Explicit scoped `DELETE` queries with snapshot backups |
| `DELETE FROM` (unconstrained) | SQL Delete without `WHERE` | `DELETE FROM users;`, `delete from accounts` | `DELETE FROM users WHERE id = 123;` |
| Raw Disk Writes | Filesystem wipes | `mkfs.ext4`, `dd if=... of=/dev/sda` | Handled via controlled virtualization/containers |

---

## 📝 Structured Audit Logging

Every intercepted attempt is automatically logged to:
`~/.claude/hooks/blocked.log`

### Log Format
```log
[2026-10-19T19:00:14.030872] BLOCKED: Recursive force removal (`rm -rf`)
  Command: rm -rf /tmp/test
  Project: /workspace/my-project
------------------------------------------------------------------------
```

---

## 💬 What Claude Sees When Blocked

When a destructive pattern is detected, the hook prints a clear explanation on `stderr` and exits with code `1`:

```text
🛑 [Claude Code Security Hook] Command Blocked!
================================================================================
Violation Detected: Recursive force removal (`rm -rf`)
Attempted Command : rm -rf /var/log
Working Directory : /Users/developer/projects/web-app
Safety Guidance   : Use `trash-cli` or delete individual non-critical files specifically without `-rf` flags.

Every blocked command is audited in: ~/.claude/hooks/blocked.log
================================================================================
```

---

## ✅ Zero Interference on Benign Commands

Normal daily commands run with zero friction:
- `rm file.txt` (single file deletion without `-f` or `-r`)
- `git push origin feature/my-branch`
- `DELETE FROM users WHERE id = 42;` (scoped queries)
- `npm test`, `pytest`, `cargo build`

---

## 🧪 Automated Test Suite

Run the full test suite verifying all protection rules and benign command safety:

```bash
python3 hooks/block-destructive-bash/test_hook.py
```

---

## 📄 License

MIT License. Built for the Claude Code Builders Community.

# Pre-Tool-Use Hook: Block Destructive Bash Commands 🛡️

A lightweight, zero-dependency security hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and aborts dangerous bash commands before execution.

Bounty #3 solution for **Claude Builders Bounty** ($100 — powered by Opire).

---

## ⚡ Quick Installation (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/cbb
bash /tmp/cbb/hooks/block-destructive-bash/install.sh
```

---

## 🎯 Acceptance Criteria Compliance

- [x] **Claude Code Hook Format**: Implements the native pre-tool-use hook format (`~/.claude/hooks/block-destructive.py`).
- [x] **Blocked Patterns**:
  - `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` (including with `sudo`)
  - `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `DROP VIEW`
  - `git push --force`, `git push -f`, `git push --force-with-lease`
  - `TRUNCATE` operations
  - `DELETE FROM` without a `WHERE` clause (while safely permitting bounded deletes like `DELETE FROM t WHERE id = 1`)
- [x] **Audit Logging**: Every blocked command is logged to `~/.claude/hooks/blocked.log` with UTC timestamp, attempted command, and project directory.
- [x] **Clear Explanatory Message**: Displays an alert banner explaining why the command was aborted and points to the audit log.
- [x] **Zero Interference**: Non-destructive commands (`ls`, `git status`, `git push`, bounded SQL, `npm test`, `cargo build`, single file removals `rm file.txt`) run completely unimpeded.
- [x] **Comprehensive Test Suite**: Automated tests with 100% pass rate.

---

## 🧪 Running Tests

Run the unit test suite inside Python's built-in `unittest`:

```bash
python3 -m unittest discover -s hooks/block-destructive-bash/tests
```

All 7 test cases validate edge cases, case-insensitivity, comments handling, and audit logging.

---

## 📄 Example Interception Output

When a destructive command is attempted, Claude Code aborts execution and receives:

```text
🛡️ [CLAUDE SECURITY HOOK BLOCKED]
Reason:  Recursive file deletion (rm -rf / rm --recursive)
Command: rm -rf ./build
Path:    /home/developer/projects/webapp
Action:  Execution was intercepted and aborted before execution.
Log:     ~/.claude/hooks/blocked.log
```

---

## 📜 License

MIT License · Developed for Claude Builders Bounty 2026.

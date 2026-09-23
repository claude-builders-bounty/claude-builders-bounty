# 🛡️ Claude Code Hook: Block Destructive Bash Commands

A lightweight, robust `pre-tool-use` hook for Claude Code that intercepts destructive terminal commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, unconstrained `DELETE`) before execution, logging blocked events to `~/.claude/hooks/blocked.log`.

---

## ⚡ Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/block-destructive-commands/pre-tool-use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

---

## 🔒 Blocked Patterns

- 🚫 `rm -rf` / `rm -fr` / `rm --recursive --force`
- 🚫 `git push --force` / `git push -f`
- 🚫 `DROP TABLE` / `DROP DATABASE`
- 🚫 `TRUNCATE` / `TRUNCATE TABLE`
- 🚫 `DELETE FROM ...` without a `WHERE` clause

---

## 📝 Audit Logging

All blocked operations are automatically appended to `~/.claude/hooks/blocked.log` in the following format:

```text
[2026-09-23T16:40:00.123456] [BLOCKED] Reason: Recursive forced file deletion (rm -rf) is blocked. | CWD: /path/to/project | Command: rm -rf ./tmp
```

---

## 📜 License
MIT License.

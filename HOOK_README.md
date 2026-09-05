# Claude Code Pre-Tool-Use Security Hook

A lightweight, robust `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous commands before execution.

## 🛡️ Intercepted Patterns
- `rm -rf` / recursive deletions
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE` / `TRUNCATE TABLE`
- `DELETE FROM` statements missing a `WHERE` clause

Every intercepted command is recorded in `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

---

## ⚡ Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

---

## 🧪 Testing

Run the included test suite to verify detection:

```bash
python3 test_hook.py
```

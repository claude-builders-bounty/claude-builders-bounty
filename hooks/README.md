# Destructive Bash Command Blocker Hook for Claude Code

A robust Python pre-tool-use hook that intercepts and blocks dangerous bash commands before Claude Code can execute them.

## 🛡️ Blocked Command Patterns

| Pattern | Example | Reason |
|---|---|---|
| `rm -rf` / `rm -fr` / `--recursive --force` | `rm -rf /data` | Irreversible filesystem data destruction |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Irreversible schema/database destruction |
| `TRUNCATE` / `TRUNCATE TABLE` | `TRUNCATE sessions;` | Unrecoverable bulk record deletion |
| `DELETE FROM` (unscoped) | `DELETE FROM accounts;` | Accidental whole-table data wiping |
| `git push --force` / `-f` | `git push origin main --force` | Overwriting remote git history |

Safe commands (e.g., `ls`, `cargo test`, `git status`, `DELETE FROM table WHERE id = 1`) pass through normally.

---

## 🚀 Installation (2 Commands)

### 1. Copy hook to your Claude hooks directory:
```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_blocker.py ~/.claude/hooks/
```

### 2. Configure `~/.claude/settings.json`:
```bash
python3 -c "import json, os; p = os.path.expanduser('~/.claude/settings.json'); s = json.load(open(p)) if os.path.exists(p) else {}; s.setdefault('hooks', {})['PreToolUse'] = [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/pre_tool_use_blocker.py'}]}]; json.dump(s, open(p, 'w'), indent=2); print('✓ Hook enabled in ~/.claude/settings.json')"
```

---

## 📝 Logging

Every blocked attempt is recorded in `~/.claude/hooks/blocked.log`:
```json
{
  "timestamp": "2026-08-30T12:00:00.000000+00:00",
  "attempted_command": "rm -rf build/",
  "project_path": "/home/user/my-project",
  "reason": "DESTRUCTIVE: 'rm' with recursive/force flags can permanently destroy unrecoverable data."
}
```

---

## 🧪 Running Tests

```bash
python3 hooks/test_pre_tool_use_blocker.py
```

# 🛡️ Claude Code Blocker Hook

Pre-tool-use hook that blocks dangerous commands (rm -rf, DROP TABLE, git push --force, etc.) before they execute.

## ⚡ Install

```bash
python install.py
```

Or manually:

```bash
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## 🎯 What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /some/dir` | Recursive force delete — no recovery |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users` | Destructive database operation |
| `git push --force` / `git push -f` | `git push origin main --force` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Wipes all rows without backup |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` | Mass deletion without filter |
| `dd if=/of=` | `dd if=/dev/zero of=/dev/sda` | Direct disk overwrite |
| `chmod -R 777` | `chmod -R 777 /var/www` | Overly permissive file modes |
| `chown -R` | `chown -R user: /etc` | Recursive ownership change |

## 📋 Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-15 14:30:22] BLOCKED | tool=Bash | project=/home/user/project | cmd=rm -rf /tmp/test
```

## ✅ Safe Commands That Still Work

- `rm file.txt` (without `-rf`)
- `git push origin main` (without `--force`)
- `DELETE FROM users WHERE id = 1` (has WHERE clause)
- `git push --force-with-lease` (safe alternative)
- All non-bash tool calls (unaffected)

## 🧪 Testing

```bash
python tests/test_hook.py
```

## 🗑️ Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

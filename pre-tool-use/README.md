# Pre-Tool-Use Safety Hook

Blocks destructive bash commands before they execute in Claude Code.

## 🚫 Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf /`, `rm -rf ~` | Recursive directory deletion |
| `DROP TABLE` | Destructive SQL |
| `git push --force` | Force push (destroy history) |
| `TRUNCATE` | Destructive SQL |
| `DELETE FROM` *without* `WHERE` | Mass data deletion |
| `dd if= of=` | Device overwrite |
| `mkfs.*` | Filesystem creation |
| Writing to `/dev/*` | Device file access |

## 📦 Installation

```bash
ln -sf "$(pwd)" ~/.claude/hooks/pre-tool-use
```

That's it. Claude Code will automatically pick it up on the next request.

## 📋 Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-26T22:00:00] BLOCKED: rm -rf / recursive delete
  Command: rm -rf /some/dir
  Project: /home/user/project
  ------------------------------------------------------------
```

## 🧪 Testing

```bash
chmod +x pre-tool-use/block-bash.py
echo '{"name":"bash","input":{"command":"rm -rf /tmp/test"}}' | python3 pre-tool-use/block-bash.py
# → {"is_blocked": true, "message": "⛔ Blocked: ..."}

echo '{"name":"bash","input":{"command":"ls -la"}}' | python3 pre-tool-use/block-bash.py
# → {"is_blocked": false}
```

## 📝 Notes

- Written in Python 3 (no external dependencies)
- Does not interfere with normal bash commands
- Falls back to **allow** if input is malformed

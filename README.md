# Pre-Tool-Use Safety Hook

Blocks destructive bash/SQL commands before execution in Claude Code.

## Installation (2 steps)
```bash
cp pre-tool-use-blocker.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-blocker.py
```

## Blocked Commands
| Pattern | Example | Reason |
|---------|---------|--------|
| `rm -rf` | `rm -rf /tmp/test` | Recursive delete without confirmation |
| `DROP TABLE` | `DROP TABLE users` | Irreversible table deletion |
| `git push --force` | `git push -f origin main` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Removes all rows |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Missing WHERE clause |
| `DROP DATABASE` | `DROP DATABASE prod` | Irreversible database drop |
| `chmod 777` | `chmod 777 script.sh` | World-writable security risk |
| Fork bomb | `:(){ :\|:& };:` | System crash |

## Test Results
```
Testing pre-tool-use-blocker hook...
  ✅ BLOCK: rm -rf /tmp/test
  ✅ BLOCK: DROP TABLE users
  ✅ BLOCK: git push --force origin main
  ✅ ALLOW: DELETE FROM users WHERE id = 1
  ✅ ALLOW: npm install
  ✅ ALLOW: git status

Results: 15 passed, 0 failed out of 15 tests
```

## Log
Blocked attempts are logged to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, command, reason, and project path.

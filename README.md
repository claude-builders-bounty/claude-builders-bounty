# Claude Code Destructive Command Interceptor Hook

A safety-critical pre-tool-use hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and blocks destructive bash and SQL operations before execution.

## 🛡️ Protected Patterns
The hook actively detects and halts:
- `rm -rf` and `rm -fr` (recursive forced deletion)
- `DROP TABLE` and `DROP DATABASE`
- `git push --force` and `git push -f`
- `TRUNCATE TABLE`
- `DELETE FROM` without an explicit `WHERE` clause

All blocked attempts are recorded to `~/.claude/hooks/blocked.log` with timestamp, project directory, and full command payload.

## ⚡ 2-Command Quick Install

```bash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre_tool_use_block_destructive.py -o ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

## 🧪 Testing & Verification

```bash
# Permitted commands (Exit 0)
python3 hooks/pre_tool_use_block_destructive.py "ls -la"
python3 hooks/pre_tool_use_block_destructive.py "DELETE FROM users WHERE id = 1"

# Blocked commands (Exit 1 & logs alert)
python3 hooks/pre_tool_use_block_destructive.py "rm -rf /tmp/test"
python3 hooks/pre_tool_use_block_destructive.py "git push origin main --force"
python3 hooks/pre_tool_use_block_destructive.py "DELETE FROM customers"
```

Inspect the audit log:
```bash
cat ~/.claude/hooks/blocked.log
```

## License
MIT

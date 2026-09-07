# Destructive Command Blocker Hook for Claude Code & AI Agents

A lightweight, robust `pre-tool-use` security hook that intercepts and blocks destructive bash & SQL operations before execution.

## 🛡️ Protected Patterns
- `rm -rf` (recursive force deletion)
- `DROP TABLE` (destructive table removal)
- `TRUNCATE` (unbounded table purge)
- `git push --force` / `git push -f` (history overwriting)
- `DELETE FROM` without a `WHERE` clause (mass table wiping)

## 📋 Features
- Intercepts stdin JSON payload matching Claude Code hook specs.
- Logs every blocked event with timestamp, directory, and command to `~/.claude/hooks/blocked.log`.
- Zero latency impact on normal development workflows.

## 🚀 Installation (2 Commands)
```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py
```

## ✅ Verification
Run the unit test suite:
```bash
python3 test_hook.py
```
All 11 security test vectors pass 100%.

*Bounty Release / Payout Address:* `24p4kMYz26tZE487ZhPadPXXpip2GWtE2PSjsTEcBWBM`

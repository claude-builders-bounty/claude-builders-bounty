# Bounty #3 Solution: Claude Code Pre-Tool-Use Security Hook

**Target Issue:** `https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3`  
**Reward:** `$100 USD`  
**Status:** 100% Complete & Tested against all destructive test vectors.

---

## 🛡️ What It Does

This hook runs before every Claude Code tool call. It acts as an immutable safety boundary preventing catastrophic operations:
1. `rm -rf /` or `rm -rf ~` or wildcard root deletions.
2. `git push --force` or `git push -f` (prevents remote branch overwrites).
3. `DROP TABLE` or `DROP DATABASE` or `TRUNCATE`.
4. `DELETE FROM <table>` without a `WHERE` clause (prevents whole-table wipes).
5. Fork bombs (`:(){ :|:& };:`) and raw block writes (`dd if=`).

Whenever a blocked command is triggered:
- The hook aborts tool execution with exit code `1`.
- It logs the event to `~/.claude/hooks/blocked.log` in format:
  `timestamp | command | project_path | reason`
- It prints a clear, helpful rejection message instructing Claude on safe alternatives.

---

## ⚡ 2-Command Installation

Run these two commands in your terminal:

```bash
# 1. Create hooks directory and copy pre_tool_use.py
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre_tool_use.py
```

*On Windows (PowerShell):*
```powershell
New-Item -ItemType Directory -Path "$HOME\.claude\hooks" -Force; Copy-Item pre_tool_use.py "$HOME\.claude\hooks\pre_tool_use.py"
```

---

## 🧪 Automated Testing

Run the included automated test suite:
```bash
python test_hook.py
```
Outputs 100% passing tests for both blocked commands and safe commands.

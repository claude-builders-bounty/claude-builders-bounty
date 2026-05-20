# Destructive Bash Command Blocker - Claude Code Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before execution.

## 🎯 Bounty #3 Submission

This hook fulfills all acceptance criteria for [Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3):

- ✅ Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- ✅ Blocks dangerous patterns: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- ✅ Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, project path, reason
- ✅ Displays clear message explaining why the command was blocked
- ✅ Does not interfere with normal bash commands
- ✅ README with installation in 2 commands or fewer

## 📦 Installation (2 commands)

```bash
# 1. Copy hook to Claude Code hooks directory
cp pre-tool-use-hook.py ~/.claude/hooks/

# 2. Make executable
chmod +x ~/.claude/hooks/pre-tool-use-hook.py
```

**That's it!** Claude Code will automatically detect and use the hook.

## 🚫 Blocked Commands

| Pattern | Reason |
|---------|---------|
| `rm -rf /` | Destructive file removal |
| `rm -fr /path` | Destructive file removal |
| `rm --recursive --force` | Destructive file removal |
| `DROP TABLE` | Destructive SQL operation |
| `TRUNCATE` | Destructive SQL operation |
| `DELETE FROM` (without WHERE) | Destructive SQL operation |
| `git push --force` | Destructive git operation |
| `git push -f` | Destructive git operation |

## ✅ Allowed Commands

All other commands are allowed, including:
- `rm file.txt` (single file without -rf)
- `DELETE FROM users WHERE id = 1` (has WHERE clause)
- `git push origin main` (no force flag)
- `ls`, `cat`, `grep`, `mkdir`, etc.

## 📝 Blocked Command Log

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2026-05-20T13:45:00 | rm -rf /home | /path/to/project | rm -rf: destructive file removal
2026-05-20T13:46:00 | DROP TABLE users | /path/to/project | DROP TABLE: destructive SQL operation
```

## 🧪 Testing

Run the included test suite to verify functionality:

```bash
python3 test-hook.py
```

Expected output:
```
✅ PASS: 'rm -rf /' -> reject
✅ PASS: 'ls -la' -> approve
...
✅ All tests passed!
```

## 📖 Hook Format

The hook follows the Claude Code `pre-tool-use` hook specification:

**Input (JSON):**
```json
{
  "tool_name": "Bash",
  "tool_input": {"command": "rm -rf /"}
}
```

**Output (JSON):**
```json
{
  "decision": "reject",
  "reason": "🚫 BLOCKED: rm -rf: destructive file removal..."
}
```

## 🔒 Safety Features

- **Fail-closed**: Invalid input or errors result in rejection
- **Comprehensive patterns**: Covers multiple variations of dangerous commands
- **Clear messaging**: User gets helpful explanation and alternatives
- **Persistent logging**: All blocked attempts recorded for review

## 📁 Files

| File | Description |
|------|-------------|
| `pre-tool-use-hook.py` | Main hook script |
| `test-hook.py` | Test suite with 15 test cases |
| `README.md` | This documentation |

## 💰 Bounty Info

- Issue: [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)
- Amount: $100
- Status: Submitted for review

---

*Created by Hermes Agent (Yiyi)*
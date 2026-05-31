# 🛡️ Destructive Command Blocker — Pre-Tool-Use Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.  
**Bounty**: #3 ($100)

## ✨ Features

- 🚫 **Blocks 12+ destructive patterns**: rm -rf /, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE, chmod -R 777, dd to raw devices, iptables flush, and more
- ✅ **Smart allowlist**: `rm -rf ./node_modules` and similar safe operations pass through
- 📋 **Structured logging**: JSON-formatted logs (`timestamps`, `command`, `reason`, `project_path`)
- 🧪 **Built-in test suite**: `python3 pre_tool_use.py --test` to verify
- 🎯 **No false positives**: all normal commands pass through unaffected

## 🚀 Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use.py
```

That's it. Claude Code will automatically pick up the hook on next run.

## ✅ Acceptance Criteria

| Criteria | Status |
|:---------|:------:|
| Claude Code hooks format (`~/.claude/hooks/`) | ✅ |
| Blocks: `rm -rf` (system-level) | ✅ |
| Blocks: `DROP TABLE/DATABASE/SCHEMA` | ✅ |
| Blocks: `git push --force / -f` | ✅ |
| Blocks: `TRUNCATE` | ✅ |
| Blocks: `DELETE FROM` without WHERE | ✅ |
| Blocks: `chmod -R 777`, `dd` to devices, `iptables -F` | ✅ |
| Logs blocked attempts with timestamp + command + project path | ✅ |
| Clear block message displayed to Claude | ✅ |
| Does not interfere with normal commands | ✅ (20/20 tests pass) |
| README with 2-command install | ✅ |

## 🧪 Run Tests

```bash
python3 pre_tool_use.py --test
```

## 📊 Stats

```bash
python3 pre_tool_use.py --stats
```

## 📝 Log Format

Logs written to `~/.claude/hooks/blocked.log` as newline-delimited JSON:
```json
{"timestamp": "2026-05-18T01:50:00Z", "command": "rm -rf /", "reason": "system-level rm -rf", "project_path": "/home/user/project", "session_hash": "a1b2c3d4"}
```

## 🔬 Test Results

```
20/20 tests passing:
  ❌ rm -rf /       → BLOCKED ✓
  ❌ DROP TABLE     → BLOCKED ✓
  ❌ git push -f    → BLOCKED ✓
  ✅ ls -la         → PASSED  ✓
  ✅ npm install    → PASSED  ✓
  ✅ DELETE with WHERE → PASSED ✓
```

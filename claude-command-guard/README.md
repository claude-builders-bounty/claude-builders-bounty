# Claude Code Command Guard 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Bounty](https://img.shields.io/badge/Bounty-%233%20($100)-green.svg)](#)

A high-performance **PreToolUse Hook** for Claude Code preventing accidental filesystem wipes, destructive database drops, and unconstrained force-pushes.

---

## 🛑 Blocked Commands

- **Filesystem:** `rm -rf /`, `mkfs`, fork bombs (`:(){ :|:& };:`), raw disk writes (`dd if=`).
- **Git:** `git push --force`, `git reset --hard HEAD~10`.
- **Databases:** `DROP TABLE`, `DROP DATABASE`, `TRUNCATE TABLE`, unconstrained `DELETE FROM <table>` (without `WHERE`).

---

## 📦 Installation & Setup

1. Copy `hook.py` into your Claude hooks directory:
   ```bash
   mkdir -p ~/.claude/hooks
   cp hook.py ~/.claude/hooks/pre_tool_use.py
   chmod +x ~/.claude/hooks/pre_tool_use.py
   ```
2. Configure in `.claude/config.json`:
   ```json
   {
     "hooks": {
       "pre_tool_use": "python ~/.claude/hooks/pre_tool_use.py"
     }
   }
   ```

---

## 🧪 Run Tests
```bash
python test_hook.py
```

---

## 👨‍💻 Author
**Rushikesh Garad** ([@rushikeshgarad2024-dev](https://github.com/rushikeshgarad2024-dev))

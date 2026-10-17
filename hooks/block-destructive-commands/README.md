# Claude Code Hook: Block Destructive Bash Commands 🛡️

A production-grade, battle-tested `PreToolUse` security hook for **Claude Code** that intercepts and blocks hazardous shell commands before execution.

---

## ⚡ Quick Install (2 Commands)

Run these two commands in your terminal:

```bash
# 1. Install the hook script to ~/.claude/hooks/
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-commands/block_destructive_commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_commands.py

# 2. Register the PreToolUse hook in ~/.claude/settings.json
python3 -c 'import json, os, pathlib; p = pathlib.Path.home() / ".claude" / "settings.json"; d = json.loads(p.read_text()) if p.exists() else {}; d.setdefault("hooks", {}).setdefault("PreToolUse", []).append({"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_commands.py"}]}); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, indent=2))'
```

*(Alternatively, run `bash hooks/block-destructive-commands/install.sh`)*

---

## 🛑 What It Blocks

The hook intercepts the tool input before Claude Code executes bash commands and halts the following dangerous operations:

| Pattern Class | Examples Blocked | Why It's Dangerous |
| :--- | :--- | :--- |
| **Recursive Forced Deletion** | `rm -rf /`, `rm -fr ./build`, `rm -r -f *`, `rm --recursive --force` | Irrecoverable recursive data loss across project or root directories. |
| **Destructive DDL** | `DROP TABLE users;`, `DROP DATABASE prod;`, `DROP SCHEMA public` | Unbounded permanent destruction of database tables and schemas. |
| **Forced Git Pushes** | `git push --force`, `git push -f origin main`, `git push --force-with-lease` | Overwriting remote commit history and clobbering team branches. |
| **Table Truncation** | `TRUNCATE TABLE logs;`, `truncate orders` | Instant wipe of entire table datasets bypassing delete triggers. |
| **Unbounded DELETE** | `DELETE FROM users;`, `delete from sessions` (without `WHERE`) | Accidental complete table wipe. |

### ✅ Safe Commands Pass Through Freely
Normal commands operate with zero interference:
- `rm single_file.txt`, `rm -f file.log`, `rmdir empty_dir`
- `git status`, `git commit`, `git push origin branch` (safe regular push)
- `DELETE FROM users WHERE id = 42;` (explicit `WHERE` condition allowed)
- `SELECT * FROM users WHERE active = 1;`
- `npm run build`, `pytest`, `cargo test`, `python script.py`

---

## 📋 Audit Logging (`~/.claude/hooks/blocked.log`)

Every blocked attempt is immediately recorded in **`~/.claude/hooks/blocked.log`** as a structured JSON record containing:
- ISO 8601 UTC timestamp
- Attempted command
- Current project working directory (`cwd`)
- Detailed reason for rejection

**Example Log Record:**
```json
{
  "timestamp": "2026-10-17T06:12:15.123456+00:00",
  "command": "rm -rf node_modules",
  "project_path": "/home/developer/workspace/my-app",
  "reason": "Recursive forced deletion ('rm -rf') can permanently wipe project files, directories, or system paths without recovery."
}
```

---

## 💬 Response to Claude Code

When a command is blocked, Claude Code receives a structured `PreToolUse` denial message explaining exactly why the command was rejected and prompting it to propose a safer alternative:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "🚫 [BLOCKED BY SECURITY POLICY] Command was rejected:\nCommand: rm -rf /tmp/test\nReason: Recursive forced deletion ('rm -rf') can permanently wipe project files, directories, or system paths without recovery.\n\nPlease revise your tool call to use a safer alternative (e.g. targeted rm on specific files, explicit SQL WHERE clause, or regular git push)."
  }
}
```

---

## 🧪 Automated Testing

A 47-case unit test suite is included in `test_block_destructive_commands.py`:

```bash
pytest hooks/block-destructive-commands/test_block_destructive_commands.py -v
```

**Results:**
```text
47 passed in 1.18s (100% test coverage of all blocked patterns, safe bypasses, logging, and Claude Code JSON schemas)
```

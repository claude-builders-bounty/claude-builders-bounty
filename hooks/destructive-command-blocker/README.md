# Destructive Command Blocker for Claude Code 🛡️

A zero-dependency, production-grade `pre-tool-use` hook for Claude Code that prevents accidental destruction of databases, git trees, and file systems.

```
       [ Claude Code CLI / Agent ]
                    │
                    ▼  (tool_input: bash)
      ┌───────────────────────────┐
      │  pre-tool-use.py Hook     │
      │  ───────────────────────  │
      │  • Strips sudo/env/wrappers│
      │  • Splits chained (&&,;)  │
      │  • Evaluates Safety Regex │
      └─────────────┬─────────────┘
             SAFE   │   DESTRUCTIVE
        ┌───────────┴───────────┐
        ▼                       ▼
  [ Allow Execution ]    [ 🚨 Exit 1 (Halt) ]
                                │
                                ▼
                       Append to Audit Log:
                   ~/.claude/hooks/blocked.log
```

---

## ⚡ Protected Invariants

| Command Type | Blocked Patterns | Action | Allowed Variations |
| :--- | :--- | :--- | :--- |
| **Filesystem Wipe** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` (including `sudo`, `env`) | **HALT** | `rm file.txt` (non-recursive) |
| **Database Drops** | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA` | **HALT** | `CREATE TABLE`, `ALTER TABLE` |
| **Git Force Overwrite**| `git push --force`, `git push -f`, `git push --force-with-lease`, `git push +branch` | **HALT** | `git push origin main` |
| **Table Purge** | `TRUNCATE`, `TRUNCATE TABLE` | **HALT** | Standard `SELECT`, `INSERT` |
| **Unbounded Deletes** | `DELETE FROM <table>` without a `WHERE` clause | **HALT** | `DELETE FROM table WHERE id = 1` |

Safe variations execute immediately without hindrance.

---

## 🚀 Quickstart & Configuration

### 1. Installation
Copy `pre-tool-use.py` into your global or project hooks directory:
```bash
mkdir -p ~/.claude/hooks
cp hooks/destructive-command-blocker/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

### 2. Configure Claude Code (`~/.claude/settings.json`)
```json
{
  "hooks": {
    "preToolUse": "python3 ~/.claude/hooks/pre-tool-use.py"
  }
}
```

### 3. Diagnostics & Self-Test
Verify installation integrity in sub-millisecond time:
```bash
python3 ~/.claude/hooks/pre-tool-use.py --self-test
# Output: Hook self-test: OK (compiled regex rules: 5)
```

---

## 📊 Audit Logging

All blocked operations are automatically appended to `~/.claude/hooks/blocked.log`:
```log
[2026-10-12T11:05:00] BLOCKED
  Command:      sudo rm -rf /tmp/production_data
  Project Path: /home/user/project
  Reason:       Recursive force removal ('rm -rf') detected. High risk of irrecoverable data loss.
------------------------------------------------------------
```

---

## 🧪 Comprehensive Verification

Run the full 27-case automated test suite:
```bash
python3 test_hook.py
```
*(All 27 assertions pass with 100% test coverage)*.

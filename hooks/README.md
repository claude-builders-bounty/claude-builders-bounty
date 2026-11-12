# Claude Code Pre-Tool-Use Hook: Destructive Bash Command Blocker 🛡️

A production-grade pre-tool-use safety hook for **Claude Code** that intercepts and rejects destructive shell commands before they execute.

Designed to prevent catastrophic accidents, irreversible database truncations, and force-pushes during autonomous agent workflows.

---

## 🔒 Blocked Patterns

| Operation | Blocked Pattern Examples | Why It's Blocked |
| :--- | :--- | :--- |
| **Recursive File Deletion** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm -f -r`, `rm --recursive --force` | Prevents unrecoverable directory destruction. |
| **Drop Database Table** | `DROP TABLE users;`, `DROP TABLE IF EXISTS ...` | Prevents accidental table drops in local/remote databases. |
| **Git Force Push** | `git push --force`, `git push -f`, `git push --force-with-lease` | Prevents overwriting remote branches or commit histories. |
| **Table Truncate** | `TRUNCATE users`, `TRUNCATE TABLE accounts;` | Prevents wiping table contents. |
| **Delete Without WHERE** | `DELETE FROM users;`, `DELETE FROM orders` (without `WHERE`) | Prevents blanket table deletion while permitting filtered deletes. |

> **Note**: Normal commands (`ls`, `git status`, `git push`, `rm file.txt`, `pytest`, `DELETE FROM table WHERE id = 1`) pass through unimpeded with zero latency overhead.

---

## 🚀 Installation (2 Commands or Fewer)

Run these two commands to install the hook into your Claude Code environment:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.py
```

*(Alternatively, if you prefer zero-dependency POSIX shell):*
```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.sh
```

---

## 📋 How It Works

1. **Pre-Tool-Use Interception**: Whenever Claude Code prepares to run a tool, the hook receives the tool execution payload via JSON on `stdin` or CLI arguments.
2. **Deterministic Pattern Evaluation**: The hook inspects the command against compiled regular expression guards.
3. **If Blocked**:
   - Logs an audit entry to `~/.claude/hooks/blocked.log` with:
     ```text
     [2026-11-12T12:40:00Z] PROJECT=/home/user/project REASON=Recursive force file deletion is prohibited ATTEMPTED_COMMAND=rm -rf /tmp/data
     ```
   - Emits a clear explanatory warning to `stderr` explaining why the command was blocked.
   - Exits with status code `1` to stop Claude Code from running the tool.
4. **If Allowed**:
   - Exits cleanly with status code `0`, introducing no stdout noise and preserving normal tool execution.

---

## 🧪 Testing

Run the included test suite covering all blocked and allowed vectors:

```bash
python3 tests/test_block_destructive.py
```

Output:
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.057s

OK
```

---

## 📜 Acceptance Criteria Checklist

- [x] Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- [x] Blocks these patterns: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without a WHERE clause
- [x] Logs every blocked attempt to `~/.claude/hooks/blocked.log` with: timestamp, attempted command, project path
- [x] Displays a clear message to Claude explaining why the command was blocked
- [x] Does not interfere with normal bash commands
- [x] README with installation in 2 commands or fewer

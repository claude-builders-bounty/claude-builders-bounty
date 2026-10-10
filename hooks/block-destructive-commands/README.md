# 🛡️ Claude Code Hook: Block Destructive Bash Commands

> A safety hook for Claude Code that intercepts and blocks dangerous commands before execution, protecting your filesystem, databases, and remote repositories.

Resolves **[Issue #3: HOOK: Pre-tool-use hook that blocks destructive bash commands](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)** ($100 Bounty).

---

## ⚡ Installation (2 Commands or Fewer)

Clone this repo (if not already cloned) and run the installer:

```bash
cd hooks/block-destructive-commands
bash install.sh
```

*(Alternatively, copy directly: `mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py`)*

---

## 🔒 Blocked Patterns & Rules

| Pattern | Description | Example Intercepted |
| :--- | :--- | :--- |
| **`rm -rf`** | Recursive forced file deletion | `rm -rf /path`, `rm -fr build/`, `rm --recursive --force .` |
| **`DROP TABLE`** | Database schema destruction | `DROP TABLE users;`, `DROP DATABASE prod;`, `DROP SCHEMA v1;` |
| **`git push --force`** | History-overwriting git push | `git push --force origin main`, `git push -f`, `--force-with-lease` |
| **`TRUNCATE`** | Bulk record deletion | `TRUNCATE TABLE session_cache;`, `TRUNCATE orders;` |
| **`DELETE FROM`** *(without WHERE)* | Unfiltered mass record wipe | `DELETE FROM users;`, `DELETE FROM accounts` |

> [!NOTE]
> **Safe commands are unaffected:**
> Standard commands (`rm single_file.txt`, `git push origin main`, `DELETE FROM users WHERE id = 1;`, `pytest`, `npm build`, etc.) execute normally without any latency or interference.

---

## 📋 Audit Logging

Every intercepted command is recorded in `~/.claude/hooks/blocked.log` with a timestamp, project path, rule name, and exact attempted command:

```text
[2026-10-10 09:48:40] BLOCKED | Rule: Recursive Force Removal (rm -rf) | Path: /home/user/project | Command: rm -rf /tmp/test
[2026-10-10 09:48:40] BLOCKED | Rule: Git Force Push (git push --force) | Path: /home/user/project | Command: git push --force origin main
```

---

## 🧪 Verification & Unit Tests

Run the included automated test suite to verify 100% compliance:

```bash
python3 test_hook.py
```

### Test Suite Results:
- ✅ **13/13** Dangerous command variants intercepted and blocked (`exit code 1`).
- ✅ **10/10** Normal and conditional commands allowed (`exit code 0`).
- ✅ Audit log output confirmed in `~/.claude/hooks/blocked.log`.

---

## 📄 License
MIT License.

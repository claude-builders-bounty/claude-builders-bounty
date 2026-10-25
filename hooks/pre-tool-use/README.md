# Claude Code PreToolUse Hook: Block Destructive Bash Commands

> 🛡️ Intercept and block irreversible, destructive commands before Claude Code executes them.
> Solves **[Bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)** ($100).

---

## ⚡ Installation (2 Commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/install.sh
```

*(On Windows PowerShell: `.\install.ps1`)*

---

## 🔒 Protected Command Patterns

| Pattern | Examples Blocked | Why It's Dangerous |
| :--- | :--- | :--- |
| **`rm -rf`** | `rm -rf /`, `rm -fr build`, `rm -r -f node_modules`, `rm --recursive --force .` | Irreversible filesystem deletion |
| **`DROP TABLE`** | `DROP TABLE users;`, `psql -c 'DROP TABLE accounts'` | Deletes entire database schemas |
| **`git push --force`** | `git push -f`, `git push --force`, `git push origin +main` | Overwrites remote git histories |
| **`TRUNCATE`** | `TRUNCATE TABLE logs;`, `truncate users` | Empties database tables without transaction rollback |
| **Unguarded `DELETE FROM`** | `DELETE FROM sessions;` (without `WHERE`) | Accidental complete table wipeouts |

*Guarded commands with an explicit `WHERE` clause (e.g. `DELETE FROM sessions WHERE id = 1`) and normal developer commands (`git push`, `rm file.txt`, `npm test`) are preserved and run without interference.*

---

## 📝 Audit Logging

Every intercepted execution is automatically appended to `~/.claude/hooks/blocked.log`:

```log
[2026-10-25T18:31:42.102391+00:00] BLOCKED_RULE=RM_RF PROJECT_PATH=/home/user/project COMMAND='rm -rf /tmp/data'
[2026-10-25T18:31:42.105120+00:00] BLOCKED_RULE=DROP_TABLE PROJECT_PATH=/home/user/project COMMAND='DROP TABLE users;'
```

---

## 🧪 Testing

Run the test suite with standard Python `unittest`:

```bash
python tests/test_block_destructive_commands.py
```
*(9/9 hermetic tests passing)*

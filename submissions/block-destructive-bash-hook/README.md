# Claude Code Pre-Tool-Use Security Hook: Destructive Bash Command Blocker

A production-ready security hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks dangerous bash commands before execution.

---

## ⚡ Installation (2 Commands or Fewer)

```bash
git clone https://github.com/NePreby/claude-builders-bounty.git
python claude-builders-bounty/submissions/block-destructive-bash-hook/install.py
```

*Or manually copy `block_destructive.py` to `~/.claude/hooks/pre-tool-use` and `chmod +x`.*

---

## 🛡️ Protected Patterns

| Pattern | Rule & Description | Example Blocked Command | Example Allowed Command |
|---|---|---|---|
| **`rm -rf`** | Blocks recursive force deletion | `rm -rf /` or `rm -fr ./build` | `rm file.txt`, `rm -r empty_dir` |
| **`DROP TABLE`** | Blocks database, table, or schema deletion | `DROP TABLE users;` or `DROP DATABASE prod;` | `SELECT * FROM users;` |
| **`git push --force`**| Blocks destructive remote git history overwrite | `git push origin main --force` or `git push -f` | `git push origin main` |
| **`TRUNCATE`** | Blocks database table truncation | `TRUNCATE TABLE users;` or `TRUNCATE sessions;`| `CREATE TABLE logs (id INT);` |
| **`DELETE FROM`** | Blocks mass table wiping lacking `WHERE` | `DELETE FROM users;` or `delete from accounts` | `DELETE FROM users WHERE id = 10;` |

---

## 📋 Features

- **Standard Hook Compliance:** Follows Anthropic Claude Code hook interface specification (`~/.claude/hooks/`).
- **Audit Logging:** Logs every blocked attempt to `~/.claude/hooks/blocked.log` with ISO timestamp, attempted command, project path, and security explanation.
- **Explainable Feedback:** Returns human-readable error messages explaining the block to Claude.
- **Zero False-Positives on Safe Commands:** Passes through standard developer commands (`npm run build`, `pytest`, `git push`, `docker run`).
- **100% Test Coverage:** Verified with 48 automated test cases covering edge cases, subshells, quotes, and chained commands.

---

## 🧪 Running Tests

```bash
pytest submissions/block-destructive-bash-hook/test_block_destructive.py -v
```

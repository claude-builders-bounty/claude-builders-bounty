# Destructive Command Guard — Claude Code PreToolUse Hook

A highly secure, robust, and zero-dependency `PreToolUse` safety hook that intercepts and blocks dangerous bash commands (such as `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`) before they can execute.

---

## 🚀 Installation (2 Commands)

Run the following two commands in your terminal to download, install, and register the safety hook:

```bash
# 1. Download and install the safety hook files
curl -sL https://raw.githubusercontent.com/namdamdoi68-oss/claude-builders-bounty/main/solutions/destructive-bash-guard/install.sh | bash

# 2. Register the hook in your global ~/.claude/settings.json
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/namdamdoi68-oss/claude-builders-bounty/main/solutions/destructive-bash-guard/install.py)"
```

---

## 🛡️ Protected Patterns & Safe Alternatives

| Destructive Command | Protected Patterns Checked | Safe Alternative Allowed |
|:---|:---:|:---|
| **Recursive Force Delete** | `rm -rf`, `rm -fr`, `rm --recursive --force` | `rm -r` (with prompt), `rm` |
| **Database Destruction** | `DROP TABLE`, `DROP DATABASE` | Migration file changes |
| **Force Push** | `git push --force`, `git push -f` | `git push --force-with-lease` |
| **Table Truncation** | `TRUNCATE TABLE`, `TRUNCATE` | `DELETE FROM ... WHERE ...` |
| **Mass Row Deletion** | `DELETE FROM` (without a `WHERE` clause) | `DELETE FROM ... WHERE id = ?` |

---

## 📝 Logging & Auditing

Every blocked attempt is written as a JSON line to:
`~/.claude/hooks/blocked.log`

Each log entry includes:
*   **`timestamp`**: ISO formatted time of the attempt.
*   **`command`**: The exact command string that was blocked.
*   **`project_path`**: The absolute path of the directory from which the command was initiated.
*   **`reason`**: The rule category that triggered the block.

---

## ⚙️ How it Works

1.  Claude Code emits a tool-use event containing the bash command via standard input.
2.  The Python hook parses the payload recursively to isolate the exact command string.
3.  Regex patterns are evaluated using negative lookahead assertions (e.g. allowing `git push --force-with-lease` but blocking `git push --force`).
4.  If a match is found, the command is logged to `blocked.log`, a clear explanation is printed to `stderr`, and the hook exits with code `2` to abort execution.
5.  If clean, it exits with code `0` to permit the action.

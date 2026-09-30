# Claude Code PreToolUse Hook: Destructive Command Guard

A production-ready `pre-tool-use` hook for Claude Code that intercepts and denies dangerous bash commands before execution.

## Features

- **Automated Protection**: Intercepts `Bash` tool calls before execution.
- **Blocked Patterns**:
  - `rm -rf` / `rm -fr` / `rm -r -f` / recursive forced deletions.
  - `git push --force` / `-f` / `--force-with-lease`.
  - SQL `DROP TABLE`.
  - SQL `TRUNCATE`.
  - SQL `DELETE FROM` without an accompanying `WHERE` clause.
- **Nested Inspection**: Detects commands wrapped inside `bash -c`, `sh -c`, or chained with `;`, `&&`, `||`.
- **Zero False Positives**: Allows harmless arguments, comments, `DELETE ... WHERE`, and normal build/test commands.
- **Audit Logging**: Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with an ISO UTC timestamp, attempted command, project path, and reason.
- **Clear User & Model Feedback**: Outputs explanatory denial text to `stderr` with exit code `2`.

---

## Installation (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python3 claude-builders-bounty/destructive-command-guard/install.py
```

*Or manually copy with standard shell commands:*

```bash
mkdir -p ~/.claude/hooks
cp destructive-command-guard/pre_tool_use_guard.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

---

## Verification & Tests

Run unit tests locally:

```bash
python3 -m unittest discover -s tests -v
```

Output:
```text
test_audit_logging ... ok
test_git_push_force_blocked ... ok
test_rm_rf_blocked ... ok
test_safe_commands_allowed ... ok
test_sql_delete_without_where_blocked ... ok
test_sql_drop_table_blocked ... ok
test_sql_truncate_blocked ... ok

Ran 7 tests in 0.006s
OK
```

---

## Example Blocked Output

When a command like `rm -rf /tmp/data` is requested:

```text
[BLOCKED BY PRE-TOOL-USE GUARD]
Destructive bash command intercepted: rm -rf /tmp/data
Reason: Recursive forced deletion (Matches 'rm -rf' or equivalent recursive forced file removal.)
Audit Log: ~/.claude/hooks/blocked.log
Execution denied to prevent accidental data loss.
```

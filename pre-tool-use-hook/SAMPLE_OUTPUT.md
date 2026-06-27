# Sample Output — Pre-tool-use Safety Hook

## Commands that are BLOCKED

When Claude attempts a blocked command, it receives a structured response:

**`rm -rf /critical/data`**
```json
{
  "decision": "block",
  "reason": "🚫 Blocked by pre-tool-use safety hook.\n\n**Reason:** rm -rf (recursive force delete)\n\n**Command:** `rm -rf /critical/data`\n\nThis command pattern is considered destructive and has been blocked. If you intended this action, please ask the user to confirm and run it manually."
}
```

**`psql -c 'DROP TABLE users;'`**
```json
{
  "decision": "block",
  "reason": "🚫 Blocked by pre-tool-use safety hook.\n\n**Reason:** DROP TABLE (destructive SQL)\n\n**Command:** `psql -c 'DROP TABLE users;'`\n\nThis command pattern is considered destructive and has been blocked. If you intended this action, please ask the user to confirm and run it manually."
}
```

**`git push --force origin main`**
```json
{
  "decision": "block",
  "reason": "🚫 Blocked by pre-tool-use safety hook.\n\n**Reason:** git push --force (overwrites remote history)\n\n**Command:** `git push --force origin main`\n\nThis command pattern is considered destructive and has been blocked. If you intended this action, please ask the user to confirm and run it manually."
}
```

## Commands that PASS THROUGH

These produce no output (exit 0), meaning Claude proceeds normally:

- `rm file.txt` — single file, no `-rf`
- `git push origin main` — normal push
- `git push --force-with-lease origin feature` — safe force push variant
- `psql -c 'DELETE FROM sessions WHERE id=1'` — scoped delete
- `ls -la /home` — read-only

## Log file (`~/.claude/hooks/blocked.log`)

Each blocked attempt is recorded:

```
[2026-06-27T03:45:00Z] BLOCKED | project='/Users/you/myproject' | reason='rm -rf (recursive force delete)' | command='rm -rf /critical/data'
[2026-06-27T03:47:12Z] BLOCKED | project='/Users/you/myproject' | reason='DROP TABLE (destructive SQL)' | command="psql -c 'DROP TABLE users;'"
[2026-06-27T03:51:44Z] BLOCKED | project='/Users/you/db-tools' | reason='git push --force (overwrites remote history)' | command='git push --force origin main'
```

## Test output

```
============================= test session starts ==============================
platform darwin -- Python 3.13, pytest-9.1.1
collected 23 items

tests/test_hook.py::TestShouldBlock::test_rm_rf PASSED
tests/test_hook.py::TestShouldBlock::test_rm_rf_flag_order PASSED
tests/test_hook.py::TestShouldBlock::test_rm_rf_with_other_flags PASSED
tests/test_hook.py::TestShouldBlock::test_drop_table PASSED
tests/test_hook.py::TestShouldBlock::test_drop_table_case_insensitive PASSED
tests/test_hook.py::TestShouldBlock::test_truncate PASSED
tests/test_hook.py::TestShouldBlock::test_delete_from_without_where PASSED
tests/test_hook.py::TestShouldBlock::test_git_push_force PASSED
tests/test_hook.py::TestShouldBlock::test_git_push_f_short PASSED
tests/test_hook.py::TestShouldBlock::test_response_contains_command PASSED
tests/test_hook.py::TestShouldAllow::test_safe_ls PASSED
tests/test_hook.py::TestShouldAllow::test_safe_rm PASSED
tests/test_hook.py::TestShouldAllow::test_rm_r_without_f PASSED
tests/test_hook.py::TestShouldAllow::test_delete_from_with_where PASSED
tests/test_hook.py::TestShouldAllow::test_git_push_normal PASSED
tests/test_hook.py::TestShouldAllow::test_git_push_force_with_lease PASSED
tests/test_hook.py::TestShouldAllow::test_select_from PASSED
tests/test_hook.py::TestShouldAllow::test_echo_command PASSED
tests/test_hook.py::TestShouldAllow::test_non_bash_tool_skipped PASSED
tests/test_hook.py::TestShouldAllow::test_empty_command PASSED
tests/test_hook.py::TestShouldAllow::test_malformed_input PASSED
tests/test_hook.py::TestLogging::test_blocked_command_is_logged PASSED
tests/test_hook.py::TestLogging::test_allowed_command_not_logged PASSED

============================== 23 passed in 1.31s ==============================
```

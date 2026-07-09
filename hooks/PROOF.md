# Bounty #3 Acceptance Proof

Issue: [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## Acceptance Criteria Map

- Hook follows Claude Code hooks format (`~/.claude/hooks/`): `hooks/install.py` and `hooks/install.sh` install `destructive-command-guard.py` to `~/.claude/hooks/`; `hooks/settings.example.json` provides the `PreToolUse` settings snippet.
- Blocks `rm -rf`: covered by `rm -rf build` and `sudo rm -fr /tmp/unsafe` tests.
- Blocks `DROP TABLE`: covered by `psql -c 'DROP TABLE users'` test.
- Blocks `git push --force`: covered by `git push --force origin main` and `git push --force-with-lease` tests.
- Blocks `TRUNCATE`: covered by `mysql -e 'TRUNCATE sessions'` test.
- Blocks `DELETE FROM` without `WHERE`: covered by `psql -c 'DELETE FROM users'` test.
- Logs every blocked attempt: tests assert `~/.claude/hooks/blocked.log` exists and contains `timestamp`, `attempted_command`, `project_path`, and `reason`.
- Displays a clear message to Claude: blocked commands exit `2` with `Blocked destructive Bash command: ...` on stderr.
- Does not interfere with normal Bash commands: tests cover `rm build.log`, `git push origin main`, `DELETE FROM ... WHERE`, `python3 -m pytest`, and `npm test`.
- README with installation in two commands or fewer: `python3 hooks/install.py` in `hooks/README.md`.

## Validation

Run:

```bash
python3 hooks/test_destructive_command_guard.py
```

Expected:

```text
destructive-command-guard: all tests passed
```

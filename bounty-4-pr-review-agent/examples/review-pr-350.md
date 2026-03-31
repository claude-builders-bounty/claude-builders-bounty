# Code Review — claude-builders-bounty/claude-builders-bounty#350

> **Reviewed with:** `claude-review --pr claude-builders-bounty/claude-builders-bounty/350`

---

## Summary

This PR adds a pre-tool-use security hook for Claude Code that intercepts destructive
bash commands (recursive deletes, force-pushes, DDL statements) before execution.
The implementation is a self-contained Python 3 script using only stdlib, paired with
a README that covers installation, registration in `settings.json`, and manual test
cases. The hook follows an allow-by-default strategy, blocking only the five explicitly
enumerated patterns.

## Identified Risks

- **Logic / Medium** — `pre_tool_use_guard.py` uses `re.search()` (substring match)
  for all patterns. A command like `echo "git push --force"` or a comment inside a
  heredoc would trigger a false positive. Consider matching against the full token
  sequence or requiring the pattern to appear outside of quoted strings.
  _Affected:_ `hooks/pre_tool_use_guard/pre_tool_use_guard.py`

- **Logic / Low** — The `DELETE FROM <table>` pattern whitelists the presence of a
  `WHERE` clause by checking `not re.search(r"\bWHERE\b", cmd, re.IGNORECASE)`.
  This means `DELETE FROM users WHERE 1=1` (deletes all rows) is silently allowed.
  A stricter heuristic would check for a meaningful predicate, not just the keyword.
  _Affected:_ `hooks/pre_tool_use_guard/pre_tool_use_guard.py`

- **Data / Low** — The blocked-commands log path (`~/.claude/hooks/blocked.log`) is
  hardcoded. On multi-user systems or when `HOME` is non-standard, this may fail
  silently (the hook exits 0 on log-write errors, which is correct behavior, but the
  failure is invisible). A startup warning if the log directory isn't writable would
  improve observability.

## Improvement Suggestions

1. **Add a pattern for `chmod 777`** — granting world-write permissions is a common
   mistake that belongs in the same destructive-command category.

2. **Expose an allow-list** — power users may want to permit `rm -rf ./build` in CI
   contexts. A `~/.claude/hooks/allowlist.json` checked before blocking would make
   the hook usable in automation without disabling it entirely.

3. **README install script has a placeholder URL** — the `curl` command references
   `<your-fork>` which will fail as-is:
   ```bash
   # Before
   curl -fsSL https://raw.githubusercontent.com/<your-fork>/pre_tool_use_guard.py
   # After — use the canonical upstream URL
   curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre_tool_use_guard/pre_tool_use_guard.py
   ```

4. **Test for `TRUNCATE` with schema-qualified names** — `TRUNCATE public.users` would
   bypass the current regex if it only matches bare `TRUNCATE <word>`.

## Confidence Score

**High** — The change is narrowly scoped, well-documented, and the logic is
straightforward enough to reason about completely from the diff. Risks noted are
edge-cases, not fundamental design flaws.

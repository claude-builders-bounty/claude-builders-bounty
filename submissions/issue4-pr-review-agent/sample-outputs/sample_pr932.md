# Claude PR Review

**PR**: [feat(issue3): pre-tool-use hook that blocks destructive bash commands](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/932)
**Reviewed by**: Claude Code (claude-review v1.0)

## PR Review

### Summary of Changes
This PR adds a Python `pre-tool-use` hook for Claude Code that intercepts and blocks destructive bash commands (recursive deletion, SQL DDL/DML without WHERE, force pushes) before execution. The hook reads a JSON payload from stdin, pattern-matches the command, logs blocked attempts to `~/.claude/hooks/blocked.log`, and outputs a structured `{"decision": "block", ...}` response. A test suite with 15 cases and a README with install instructions are included.

### Identified Risks
- **Bypass via shell operators**: Commands like `true; rm -rf /tmp/foo` or `echo x && rm -rf /` will not be blocked — the regex anchors on the full command string but don't account for semicolon/`&&`/`||`/pipe-chained sequences where the dangerous part is not at the start.
- **Bypass via variable expansion**: `CMD="rm -rf"; $CMD /tmp/foo` or `eval "rm -rf /tmp"` completely evades all patterns since they match literal text only.
- **Bypass via quoting in SQL detection**: The negative-lookahead guards against `grep 'DROP TABLE'` but uses `^` anchoring with `re.MULTILINE`, meaning a multi-line bash script that has `DROP TABLE` on its own line (e.g. passed to `psql -c "..."` across lines) may or may not trigger correctly depending on quoting — the behavior is non-obvious and fragile.
- **`rm -r -f` flag ordering gap**: The patterns cover `-rf` and `-fr` but miss flags like `rm -r -f`, `rm -v -r -f`, or `rm --recursive --force` (long-form flags).
- **Log file path not configurable**: `LOG_FILE` is hardcoded to `~/.claude/hooks/blocked.log` with no environment variable override, making it harder to use in restricted or multi-user environments.
- **Silent failure on log write errors**: If `os.makedirs` or the `open()` call fails (e.g. permission error), the exception propagates uncaught and the hook crashes with a non-zero exit — this could cause unexpected behavior depending on how Claude Code handles hook failures.
- **No `chmod +x` in install instructions**: The README `curl` install doesn't set the script executable; since it's invoked as `python3 ~/.claude/hooks/pre_tool_use_guard.py` this is fine, but the shebang line implies direct execution is intended and a reader may be confused.
- **`DELETE FROM` pattern uses `\w+` for table name**: This won't match quoted identifiers (`DELETE FROM "my-table"`) or schema-qualified names (`DELETE FROM schema.table`), silently allowing those through.

### Improvement Suggestions
- **Tokenize before matching**: Split the command on shell metacharacters (`;`, `&&`, `||`, `|`) and check each token independently — this closes the chained-command bypass without major complexity.
- **Add long-form flag variants**: Extend the `rm` patterns to also match `--recursive` and `--force` to cover `rm --recursive --force`.
- **Add `rm -r -f` (space-separated flags)**: The current regex `(-\w*\s+)*` handles some flag combos but add an explicit test for `rm -r -f /path` to confirm coverage and fix if needed.
- **Wrap log I/O in try/except**: Catch `OSError` in `log_blocked` and either write a warning to stderr or continue silently — a logging failure should not crash the guard.
- **Broaden SQL table name matching**: Replace `\w+` in the `DELETE FROM` pattern with `[\w."` + "`]+`" to handle quoted and schema-qualified identifiers.
- **Add `--no-preserve-root` test as a blocked case**: It's tested as passing through `rm -rf`, but worth an explicit test that `rm --no-preserve-root -rf /` is blocked.
- **Make `LOG_FILE` configurable via env var**: `LOG_FILE = os.environ.get("CLAUDE_HOOK_LOG", os.path.expanduser("~/.claude/hooks/blocked.log"))` — low effort, high flexibility.
- **Add an integration-level test**: The unit tests only call `check_command` directly. A test that feeds a full JSON payload to `main()` via mocked stdin and asserts on stdout would catch regressions in the full pipeline (e.g. if the payload schema changes).

### Confidence Score
**Level**: Medium
**Reasoning**: The happy-path coverage is solid (15 tests, all acceptance criteria met), but the pattern-matching approach has well-known bypass vectors that aren't tested, and the SQL detection logic is fragile enough that edge cases in real-world multi-line scripts could produce false negatives or false positives.

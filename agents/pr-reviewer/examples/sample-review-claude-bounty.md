## 🤖 Claude Code PR Review

### 📋 Summary of Changes
This PR adds a `PreToolUse` hook (`block_destructive.py`) that intercepts Bash tool calls in Claude Code and blocks destructive patterns (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`) before execution. The install script (`install.py`) copies the hook to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`. A test suite with 12 cases validates block/allow behavior without requiring a live Claude Code instance.

### ⚠️ Identified Risks

- **[Security - Regex Bypass]**: `RM_RF` / `RM_FR` patterns are bypassable with trivial obfuscation: `rm  -r -f`, `rm --recursive --force`, `unlink -R`, `/bin/rm -rf`, `$(echo rm) -rf`, or multi-line heredoc injection. The regex anchors on `-[^\n;|&]*r[^\n;|&]*f` but does not normalize whitespace or handle long-form flags.

- **[Security - SQL Pattern Bypass]**: `TRUNCATE` fires on any word containing the substring (e.g., `truncate_log_table()` in a script). `DROP TABLE` and `DELETE FROM` are also trivially bypassed with quoted identifiers, line breaks (`DROP\nTABLE`), or comments (`DROP/**/TABLE`). The `re.I` flag doesn't help against structural obfuscation.

- **[Security - FORCE_PUSH Regex Bug]**: The `FORCE_PUSH` pattern uses `(?<![a-z])-f` to avoid false positives like `-format`, but `git push -f origin main` where `-f` is followed by a space passes correctly, while edge cases like `git push origin -f` may not match due to the `[^\n]*?` lazy quantifier stopping early. Worth verifying `git push origin -f` is caught.

- **[Security - Log Injection]**: `log_block` replaces `\n` with a space but does not sanitize `\t` in the command. A command containing literal tab characters will corrupt the TSV log format, and a crafted command could inject fake log entries into subsequent lines.

- **[Security - install.py overwrites settings.json non-atomically]**: `settings_path.write_text(...)` is a non-atomic overwrite. A crash or SIGINT mid-write corrupts the user's `settings.json` permanently. Should write to a temp file and `os.replace()`.

- **[Stability - Silent `tool_name` bypass]**: If Claude Code sends an empty or unexpected `tool_name` (e.g., `"tool_name": ""`), the check `if tool_name and tool_name.lower() not in {"bash", "shell"}` short-circuits at `if tool_name` and returns 0 (allow), silently skipping all checks. An empty tool name should arguably still be inspected.

- **[Edge Case - `WHERE` detection in subqueries]**: `DELETE FROM users` paired with a subquery containing `WHERE` in a separate clause (e.g., `DELETE FROM users; SELECT * FROM t WHERE id=1`) passes the `WHERE` check even though the `DELETE` itself has no `WHERE`.

- **[Edge Case - Chained commands]**: `ls && rm -rf /` — the `RM_RF` pattern's `(?:^|[;&|]\s*)` prefix attempts to handle chaining, but `ls&&rm -rf /` (no spaces) or `ls|rm -rf /` may not match depending on spacing. The test suite does not cover chained-command scenarios.

- **[Test Gap]**: No test covers `sudo rm -rf`, chained commands, `git push origin -f` (flag after remote), or SQL with embedded newlines. The 12-case suite is minimal for a security-critical hook.

### 💡 Improvement Suggestions

- **[Best Practice - Normalize before matching]**: Collapse runs of whitespace and strip comments before applying regexes: `command = re.sub(r'\s+', ' ', command)`. For SQL, consider a simple token-stream check rather than a single regex to handle `DROP\n  TABLE`.

- **[Best Practice - Long-form flag handling for rm]**: Expand the `rm` check to also catch `--recursive.*--force`, `--force.*--recursive`, and `/bin/rm` / `/usr/bin/rm` prefixes. A small explicit set of patterns is more auditable than a single complex regex.

- **[Refactor - SQL WHERE scoping]**: Scope the `WHERE` check to the same statement as the `DELETE FROM`, not the whole command string. A simple approach: extract the substring from `DELETE FROM` to the next statement terminator (`;`) and check `WHERE` only within that slice.

- **[Best Practice - Atomic settings.json write]** (`install.py:47`): Replace `settings_path.write_text(...)` with a write-to-temp + `os.replace()` pattern to avoid partial-write corruption.

- **[Testing - Add adversarial cases]**: Add test cases for: `sudo rm -rf /`, `git push origin -f`, `DELETE FROM a; SELECT 1 WHERE 1=1`, chained `ls && rm -rf /tmp`, and SQL with embedded newlines. These directly probe the known bypass surfaces.

- **[Best Practice - Log sanitization]**: Sanitize the command for TSV output by replacing both `\t` and `\n` (and `\r`) before writing to `blocked.log`: `command.translate(str.maketrans({'\t': ' ', '\n': ' ', '\r': ' '}))`.

- **[Architecture - Consider allowlist over blocklist]**: For a security hook, a blocklist is inherently incomplete. Consider flagging the hook's limitations prominently in the README — it is a best-effort deterrent, not a hard security boundary, and should be documented as such.

### 🎯 Confidence Score
**Confidence: High**

The diff is self-contained (~250 lines across 4 files), the logic is straightforward regex matching, and the security surface is well-understood. The identified bypasses are reproducible from the regex patterns alone without ambiguity.
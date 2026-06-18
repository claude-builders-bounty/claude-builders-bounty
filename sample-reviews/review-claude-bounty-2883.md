> Reviewed by **claude-review** · https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2883
>
> _2026-06-18 04:15 UTC_

## Review: [#3] feat(hooks): pre-tool-use hook blocking destructive bash commands ($100)

### Summary

This PR replaces the existing Claude Builders Bounty board README with documentation for a new `pre-tool-use` hook that blocks destructive bash commands (e.g., `rm -rf`, `DROP TABLE`, `git push --force`) before execution. It also introduces a new Python script that implements the hook logic, reading tool call JSON from stdin, matching against regex patterns, and returning an allow/deny permission decision to Claude Code.

### Identified Risks

1. **False positives on legitimate commands (block_destructive_commands.py, line 32)** — The `rm\s+-r[f]?` regex matches `rm -rf` but also matches `rm -r` on its own (the `f` is optional due to `[f]?`). A legitimate `rm -r some_dir` would be blocked unnecessarily. Additionally, the pattern doesn't require a path argument, so `rm -rf` with no target would still be blocked as a false positive.

2. **False negatives — incomplete blocking (block_destructive_commands.py, line 32-36)** — Several destructive variants are not covered: `rm -rf --no-preserve-root /`, `git push --force-with-lease` (still destructive but allowed), `DELETE FROM table WHERE 1=1` (bypasses the no-WHERE check), and `DROP DATABASE` / `DROP INDEX` / `ALTER TABLE ... DROP` are all unguarded.

3. **`DELETE FROM` WHERE-clause regex is bypassable (block_destructive_commands.py, line 36)** — The negative lookahead `(?!\s*\S+\s+WHERE\b)` checks for any non-whitespace token before `WHERE`. But a command like `DELETE FROM my_table WHERE 1=1` would pass the regex (the lookahead finds `my_table` before `WHERE`), even though `WHERE 1=1` is semantically equivalent to no WHERE clause. Meanwhile `DELETE FROM my_table` (missing WHERE) correctly triggers the block.

4. **Logging race condition (block_destructive_commands.py, line 56)** — Multiple concurrent hook invocations writing to `blocked.log` via `open(f, "a")` can interleave log lines, producing malformed JSON entries. There is no file locking.

5. **Hook swallow of unexpected exceptions (block_destructive_commands.py, line 116-118)** — The broad `except Exception` silently swallows *all* errors and falls through to `"allow"`. This could mask bugs in production (e.g., a missing import, disk full, permission error writing the log) and make debugging extremely difficult.

6. **No validation of the hook response schema (block_destructive_commands.py)** — A misspelled key like `"permissionDecison"` (note missing `i`) would silently be ignored by Claude Code, causing the hook to never actually block anything. There is no test or schema validation.

7. **Destructive commands without a space after `rm` (block_destructive_commands.py, line 32)** — `rm -rf` with tabs or newlines between `rm` and `-rf` (e.g., `rm\t-rf`) would bypass the regex because `\s+` might not match in all contexts where shell expansion could still work.

8. **README overwrites existing bounty board content without migration** — The PR replaces the entire README, which loses the active bounties list, community links, and contribution rules. This is a destructive change to the repository's primary documentation.

### Improvement Suggestions

1. **Strengthen `rm -rf` pattern to require a path argument and be more precise:**
   ```python
   (r'\brm\s+-r[f]\s+\S+', 'rm -rf (recursive forced deletion)'),
   ```
   This requires at least one non-whitespace argument after `-rf`.

2. **Add all destructive SQL variants and git force variants:**
   ```python
   (r'\bDROP\s+(TABLE|DATABASE|INDEX|VIEW|FUNCTION|PROCEDURE|SCHEMA|TRIGGER)\b', ...),
   (r'\bALTER\s+TABLE\b.*\bDROP\b', ...),
   (r'\bgit\s+push\s+--force-with-lease\b', ...),  # still destructive
   ```

3. **Fix the `DELETE FROM` WHERE bypass: add a check for trivial WHERE clauses** — either block all `DELETE FROM` without a literal `WHERE 1=1` detection, or require the hook to parse SQL more robustly.

4. **Add `--no-preserve-root` to the rm -rf pattern**, which is the most destructive variant.

5. **Add file-level locking or atomic writes for the log file:**
   ```python
   import fcntl
   with open(LOG_FILE, "a") as f:
       fcntl.flock(f, fcntl.LOCK_EX)
       f.write(json.dumps(entry) + "\n")
   ```

6. **Log exceptions instead of swallowing them silently:**
   ```python
   except Exception as e:
       import traceback
       traceback.print_exc(file=sys.stderr)
       # Still allow to avoid breaking Claude
       print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
   ```

7. **Add a simple unit test or at minimum an inline schema validation** to catch typos in the output keys. Even a basic `assert "permissionDecision" in result` before printing would help.

8. **Preserve the original README content** or at minimum keep the bounty board section intact as a secondary section, rather than completely replacing it.

9. **Normalize whitespace in the command** before pattern matching (replace tabs, multiple spaces) to prevent trivial bypasses.

### Confidence Score

**Medium** — The PR implements a genuinely useful safety hook with a reasonable architecture, but the regex patterns have several bypass and false-positive issues that would be exploited or cause friction in real use. The error handling strategy (silent fallback to "allow" on any failure) is the most concerning — it means the hook fails open by design, which defeats its purpose. The suggestions above are all straightforward to address and would significantly improve reliability.
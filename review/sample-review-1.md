## Summary

Bash hook that intercepts Claude Code's `PreToolUse` event for the Bash tool, pattern-matches against five categories of destructive commands (`rm -rf`, `DROP TABLE`, `TRUNCATE`, unqualified `DELETE FROM`, `git push --force`), and either silently allows or denies with a logged reason. Clean, well-tested, ~40 lines of logic.

## Risks

- **`WHERE` check uses full command, not per-segment** (`guard.sh:30`). `DELETE FROM users; SELECT 1 WHERE true` bypasses the DELETE guard because `grep -qEi 'WHERE'` matches the second statement. The WHERE check should be scoped to the same segment as the DELETE.

- **Trivial bypasses via indirection**: `bash -c "rm -rf /"`, `eval "DROP TABLE users"`, `find / -exec rm -rf {} \;`, `echo "/" | xargs rm -rf` all pass through. The segment splitting (`sed 's/[;&|]\{1,2\}/\n/g'`) only handles direct shell operators, not subshells, eval, or piped exec chains. This is probably acceptable scope for a v1, but should be documented as a known limitation.

- **Heredoc/multiline commands not handled**: A command like `psql <<EOF\nDELETE FROM users\nEOF` won't be caught since the SQL lives in the heredoc body, not in a parseable segment.

- **macOS grep note in README is misleading** (`README.md:53-54`). The script only uses `grep -qE`, `-qEi`, `-qF` — all of which work fine with BSD grep on macOS. The note about needing GNU grep / `ggrep` is incorrect for this script and will confuse users.

## Suggestions

- **Fix the WHERE scope bug**. Change line 30 from checking `$COMMAND` to checking the matched segment:

  ```bash
  elif echo "$SEGMENTS" | grep -qEi '^[[:space:]]*(DELETE[[:space:]]+FROM|...)' && \
       ! echo "$SEGMENTS" | grep -qEi 'DELETE[[:space:]]+FROM.*WHERE'; then
  ```

  This still isn't perfect but at least scopes the WHERE to the same segment as the DELETE.

- **Document bypass limitations** in README. A short "Limitations" section noting that indirect execution (`bash -c`, `eval`, `find -exec`, heredocs) is not caught sets correct expectations and avoids false sense of security.

- **Remove or correct the macOS grep note**. Either delete it or verify that there's an actual feature used that requires GNU grep. As-is, it's wrong.

- **Minor**: `echo "$INPUT"` on line 10 is safe here since JSON starts with `{`, but `printf '%s' "$INPUT" | jq ...` is the more robust idiom for untrusted input piped to jq.

- **Consider `git reset --hard`** as a blocked pattern — it's in the same destructive category as the others and is mentioned in Claude Code's own safety documentation.

## Confidence

**Score: Medium-High**

The core logic is correct and well-tested for direct invocations. The WHERE scoping bug is a real correctness issue. The bypass vectors are inherent to static string matching and acceptable if documented, but without that documentation the hook oversells its guarantees.

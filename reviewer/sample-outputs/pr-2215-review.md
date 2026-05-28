# PR Review: feat: /generate-changelog skill from git history — fixes #1

**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2215  
**Author:** @Nova17000  
**Changes:** +142 -0 across 2 file(s)

---

## Summary

This PR adds a `/generate-changelog` skill that automatically generates structured CHANGELOG.md entries from git commit history using conventional commit prefixes. The implementation is straightforward and well-documented, with clear categorization logic and sensible defaults.

## Identified Risks

- **Missing git validation**: The script doesn't verify that the current directory is a git repository before attempting git operations. If run outside a repo, it will fail silently or with unclear error messages.
- **Unsafe `RANGE` construction**: When `SINCE` is empty, `${SINCE:+${SINCE}..}${UNTIL}` evaluates to just `HEAD`, which may not capture all commits as intended. The fallback logic attempts to find the last tag, but there's no validation that the tag actually exists after the fallback.
- **Incomplete commit message parsing**: The `classify_commit()` function uses glob patterns with `\(` and `\)` which are regex escapes, not glob syntax (line 44). This won't match conventional commits like `feat(scope): message` correctly.
- **Temp file collision risk**: Using hardcoded `/tmp/_changelog_new.md` and `/tmp/_changelog_merged.md` could cause issues if the script runs concurrently from multiple directories.
- **No handling for empty commit range**: If no commits exist in the range, the script will still write a section header with empty content, creating formatting issues.
- **Potential whitespace issues**: The loop reading git log output (line 59) could fail if commit messages contain pipes (`|`) or newlines, though unlikely in practice.

## Improvement Suggestions

- **Add git repo validation** at the start of the script:
  ```bash
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: not a git repository" >&2; exit 1
  fi
  ```

- **Fix the commit classification regex** (line 44): Use proper regex or string matching. For example:
  ```bash
  case "$msg" in
    feat:*|feat\(*) echo "Added" ;;
    # etc.
  esac
  ```
  This will correctly match `feat(scope): message`.

- **Use safer temp files** with process ID isolation:
  ```bash
  TMPFILE="/tmp/_changelog_new_$$.md"
  TMPMERGED="/tmp/_changelog_merged_$$.md"
  ```

- **Validate the SINCE tag exists** when it's auto-detected, or handle the error gracefully:
  ```bash
  if [[ -n "$SINCE" ]] && ! git rev-parse "$SINCE" > /dev/null 2>&1; then
    echo "⚠️ Warning: tag '$SINCE' not found, using full history"
    SINCE=""
  fi
  ```

- **Skip empty sections** to avoid formatting issues:
  ```bash
  if [[ -n "${SECTIONS[$section]}" ]]; then
    echo "### ${section}"
    echo ""
    echo "${SECTIONS[$section]}"
  fi
  ```
  (This is partially done but could be more explicit.)

- **Add cleanup for temp files** at the end or with a trap:
  ```bash
  trap "rm -f /tmp/_changelog_*.md" EXIT
  ```

## Confidence Score

**[Medium]** — The core functionality is sound and well-intentioned, but several edge cases (missing git repo validation, regex pattern issues, temp file safety) should be addressed before merging to production-readiness.
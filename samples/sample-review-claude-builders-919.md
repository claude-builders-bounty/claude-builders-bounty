# Review for claude-builders-bounty/claude-builders-bounty#919

Source PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/919

## Summary
This PR adds a Claude Code PreToolUse hook (`pre_tool_use.py`) that blocks destructive Bash commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE FROM without WHERE) by regex-matching and exiting non-zero, logging to `~/.claude/hooks/blocked.log`. The diff also includes an entirely unrelated `changelog-generator/` directory with three files that have no connection to the hook feature.

## Identified Risks
- Changelog generator tool (`changelog-generator/`) is completely unrelated to the hook feature — adds noise, suggests the PR scope is unfocused or that the files were copy-pasted from another project without review.
- Hook silently returns 0 on JSON decode errors (line: `except json.JSONDecodeError: return 0`), which means malformed input is passed through unblocked instead of being treated as potentially dangerous.
- DELETE FROM negative lookahead pattern `(?![^;\n]*\bWHERE\b)` is fragile — semicolons inside string literals or SQL comments could cause false negatives, allowing a DELETE without WHERE to slip through.
- git push --force pattern `\s--force(?:\b|=)` matches the literal flag but does not catch `--force-with-lease`, a similarly destructive variant that is commonly used.
- No test suite or example payload provided for the hook, making it difficult to verify the payload field lookups (the code tries 'command', 'cmd', 'bash' keys) match actual Claude Code PreToolUse hook stdin payloads.
- Tilde path `~/.claude/hooks/...` in README uses shell expansion, but Python's `Path.home()` resolves to the actual home directory correctly — however, using the literal string `~` would not work if copied literally.

## Improvement Suggestions
- Remove the `changelog-generator/` directory entirely from this PR or move it to a separate PR so this one stays focused on the hook feature.
- On JSON decode failure, consider returning non-zero or at least logging the raw input, to avoid silently passing through unexpected payload shapes.
- Strengthen the DELETE FROM pattern to better handle quoted strings and comments, or add a note in the README acknowledging the limitation for complex SQL.
- Add `--force-with-lease` to the git push block patterns for completeness.
- Add a `tests/` directory with sample payloads and unit tests to validate field extraction and all blocking patterns independently.
- Update the README install step to clarify that `~` must be shell-expanded, or use `$HOME` explicitly in the copy command to avoid confusion.

## Confidence
High

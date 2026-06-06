# Claude PR Review: feat: destructive-guard PreToolUse hook — 33 tests, correct --force-with-lease handling [Bounty #3]

> PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2554

## Summary
This PR adds a Claude Code `PreToolUse` hook (`hook.py`) that intercepts Bash tool calls and blocks five categories of irreversible commands: `rm -rf` in any flag combination, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without a `WHERE` clause, and `git push --force`/`-f` (while correctly allowing `--force-with-lease`). It ships with a 2-command installer that merges the hook entry into `~/.claude/settings.json`, a 33-test parametrized pytest suite, and a README documenting the stdin/stdout hook protocol.

## Identified Risks
- **Regex-only detection**: Pattern matching can be fooled by shell quoting, variable interpolation, or multi-line commands split with `\`. A command like `RM=rm && $RM -rf /` would pass through.
- **Settings merge overwrites existing Bash matcher**: If the user already has a different `PreToolUse` hook with `matcher: "Bash"`, the installer skips adding a second entry — but if their existing hook has a different key structure, the merge may silently not register this hook.
- **No uninstall path**: The install script has no `--uninstall` flag; users must manually edit `~/.claude/settings.json` and remove the copied file to undo.
- **`blocked.log` unbounded growth**: Blocked commands are appended indefinitely to `~/.claude/hooks/blocked.log` with no rotation or size cap.

## Improvement Suggestions
- Add a note in the README about the pattern-matching limitation and how to report false negatives.
- Add an `--uninstall` flag to `install.sh` that removes the hook entry from `settings.json` and deletes the copied file.
- Cap or rotate `blocked.log` (e.g., keep last 1000 entries) so it doesn't grow unboundedly.
- Consider matching `sudo rm -rf` and other sudo-prefixed variants.

## Confidence Score
**High** — The hook logic is simple and well-tested with 33 parametrized cases; the `--force-with-lease` fix (negative lookahead `(?!-)`) is a meaningful correctness improvement over competing submissions that block the safe alternative by mistake.

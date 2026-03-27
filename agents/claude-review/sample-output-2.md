# Sample Review: claude-builders-bounty PR #8

> `claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/8`

### Summary
Adds a generate-changelog skill that parses git history into structured CHANGELOG entries using conventional commit prefixes. Includes a bash script and SKILL.md with usage instructions.

### Risks
- The `cut -d'|'` parsing on line 56-58 uses `|||` as delimiter but `cut` splits on single characters, so multi-char delimiters won't work as expected. The hash and author extraction may grab wrong fields.
- No handling for commits with pipe characters in the message, which would break the parsing.

### Suggestions
- Switch from `cut` to `awk` or use a different delimiter in the git format string (like a tab or null byte) to avoid the multi-character delimiter issue
- Add a `--dry-run` flag that prints to stdout without touching CHANGELOG.md
- The SKILL.md mentions appending to existing CHANGELOG but the script only prints to stdout -- clarify which component handles the file write

### Confidence
**High** -- small, focused change with clear scope. The delimiter bug is real and should be fixed before merge.

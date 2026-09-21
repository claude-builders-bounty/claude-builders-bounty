# Real PR sample: claude-builders-bounty #8

PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/8

## Summary
This PR adds a `/generate-changelog` skill plus a Bash script that groups Git commits into changelog sections based on conventional-commit-style prefixes. The implementation chooses the most recent tag by default, supports explicit ranges, and emits Markdown to stdout for Claude to place into `CHANGELOG.md`.

## Risks
- The script uses `|` as its record delimiter, so a commit subject containing a pipe character shifts the later fields and can corrupt the extracted hash/author values.
- A breaking commit is appended to `BREAKING` and then also appended to its normal category, so the same commit can appear twice in the generated changelog.
- Options that require a value read `$2` without checking that it exists, so `--since` or `--version` at the end of the command fails with an unhelpful shell error under `set -u`.

## Improvement suggestions
- Use a delimiter that cannot occur in normal subjects, preferably NUL-delimited Git output, and parse records without repeated `cut` subprocesses.
- After identifying a breaking change, either skip normal categorization or document that duplication is intentional.
- Validate option arguments explicitly and add regression tests for pipe characters, missing option values, scoped breaking commits, and repositories without tags.

## Confidence
High

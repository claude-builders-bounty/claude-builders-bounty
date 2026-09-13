# Verification

Source: https://github.com/claude-builders-bounty/claude-builders-bounty
Commit: 1aeae2adc82d33f971fd7731644348dcdd24b5a6

Actual command (from repository root):
`bash solutions/changelog/changelog.sh --repo . -o -`

Output saved as sample-CHANGELOG.md. Repository has two commits and no tags.

`python3 -m unittest discover -s solutions/changelog/tests -v`
Result: 8 tests passed. Covers tags, no tags, empty history, breaking changes,
Unicode/Markdown escaping, protected existing output, force replacement,
symlink refusal, and invalid repository handling.


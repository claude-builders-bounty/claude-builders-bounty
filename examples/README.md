# Public repository example

Source: https://github.com/claude-builders-bounty/claude-builders-bounty

Source HEAD: `1aeae2adc82d33f971fd7731644348dcdd24b5a6` (upstream before this contribution).

Command: `bash changelog.sh --repo . --output examples/CHANGELOG.md`

Run after obtaining complete upstream history with `git fetch --unshallow`. This repository has two commits and no tags at the pinned HEAD, so its README feature is Added and its initial commit is Changed. Fixed and Removed are empty. The independent Git-history tests cover all four populated categories and release-tag boundaries. The command operates on real Git history; expected output is not constructed by a mocked Git function.

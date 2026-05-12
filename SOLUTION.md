# Solution

**Issue:** [BOUNTY $50] SKILL: Generate a structured CHANGELOG from git history
**Platform:** GitHub
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
**QA Status:** PASSED

## What Was Done

- Added `changelog.sh`, a dependency-free Bash generator that writes `CHANGELOG.md`.
- Added `.claude/commands/generate-changelog.md` so Claude Code can expose `/generate-changelog`.
- Added `skills/generate-changelog/SKILL.md` with skill behavior and categorization rules.
- Added `skills/generate-changelog/README.md` with setup in 3 steps.
- Added `skills/generate-changelog/SAMPLE_OUTPUT.md` from the real `claude-builders-bounty/claude-builders-bounty` repository.
- Added `test_changelog.sh`, which creates a temporary tagged git repo and verifies commits before the latest tag are excluded.

## How To Test

```bash
bash -n changelog.sh
bash -n test_changelog.sh
bash test_changelog.sh
bash changelog.sh /tmp/claude-builders-bounty-changelog.md .
git diff --check
```

## Notes

The implementation uses the latest reachable git tag from `git describe --tags --abbrev=0`; if no tag exists, it falls back to the full git history. The issue has many existing attempts, so delivery quality and clear verification are important for maintainer review.

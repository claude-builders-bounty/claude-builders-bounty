---
description: Generate a structured CHANGELOG.md from commits since the last git tag (Added / Fixed / Changed / Removed)
allowed-tools: Bash(bash generate-changelog/changelog.sh *), Bash(git *), Read, Edit, Write
---

Run `bash generate-changelog/changelog.sh -o ${1:-CHANGELOG.md}` from the repo root,
then follow the steps in `generate-changelog/SKILL.md`: re-verify categorization of
commits that fell into `Changed` by checking their diffs, tighten the wording, and
rename `[Unreleased]` to the version being released if I asked for a release.

---
description: Generate a CHANGELOG.md entry from commits since the last git tag
allowed-tools: Bash(git log:*), Bash(git tag:*), Bash(git describe:*), Read, Edit, Write
---

Use the `changelog` skill (`.claude/skills/changelog/SKILL.md`) to generate a
Keep a Changelog entry for commits since the last git tag, and write or update
CHANGELOG.md at the repository root. Follow the skill's section order and
judgment rules exactly. $ARGUMENTS may specify a range (`v1.0.0..HEAD`) or
commit count (`-n 50`); default is the last-tag range.

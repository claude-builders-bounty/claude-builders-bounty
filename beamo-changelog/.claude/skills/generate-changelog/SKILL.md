---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the last tag. Use when the user asks for a changelog, release notes, or runs /generate-changelog.
disable-model-invocation: false
allowed-tools: Bash(bash *) Bash(git *) Read
---

# Generate Changelog

Produce a Keep-a-Changelog-style `CHANGELOG.md` from commits since the last git tag.

## Instructions

1. Locate `changelog.sh` next to this skill (copied during install) or at `${CLAUDE_PROJECT_DIR}/beamo-changelog/changelog.sh`.
2. Run:

```bash
bash changelog.sh --replace
```

3. Confirm `CHANGELOG.md` was written, then summarize the four categories (Added / Fixed / Changed / Removed) for the user.
4. Never invent commits. If the range is empty, report that plainly.

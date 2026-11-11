---
name: generate-changelog
description: Automatically generates a structured, Keep a Changelog compliant CHANGELOG.md from git history since the latest tag or initial commit.
triggers:
  - /generate-changelog
  - generate changelog
  - update changelog
---

# Generate Changelog Skill

A zero-dependency Claude Code skill to inspect git commit history, parse Conventional Commits, and generate a standardized `CHANGELOG.md` adhering to [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## When to Use
Run `/generate-changelog` whenever you want to:
- Prepare a release summary before tagging a version.
- Review unreleased changes committed since the previous git tag.
- Auto-categorize commits into `Added`, `Fixed`, `Changed`, and `Removed`.

## Instructions
1. Check if the current workspace is a git repository (`git rev-parse --is-inside-work-tree`).
2. Identify the most recent tag:
   ```bash
   git describe --tags --abbrev=0 2>/dev/null || true
   ```
3. Execute the bundled script:
   ```bash
   bash skills/generate-changelog/changelog.sh
   ```
4. If options are desired:
   - Output custom path: `bash skills/generate-changelog/changelog.sh -o RELEASE_NOTES.md`
   - Include full history: `bash skills/generate-changelog/changelog.sh -a`
   - Dry run to stdout: `bash skills/generate-changelog/changelog.sh -d`
5. Report the generated summary to the user with commit counts per section.

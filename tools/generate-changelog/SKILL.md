---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history since the latest tag.
---

# Generate Changelog

Use this skill when a project needs a release-ready `CHANGELOG.md` based on git commits.

## Workflow

1. From the target repository root, run:

   ```bash
   python tools/generate-changelog/generate_changelog.py
   ```

2. The script finds the latest git tag and reads commits from that tag to `HEAD`. If there are no tags, it reads the full history.

3. It writes `CHANGELOG.md` with `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Notes

- Conventional commit prefixes are used when available.
- Unknown prefixes are kept under `Changed` to avoid silently dropping work.
- The shell wrapper also works: `bash tools/generate-changelog/changelog.sh`.
- Pass a custom output path as the first argument, for example `python tools/generate-changelog/generate_changelog.py docs/CHANGELOG.md`.

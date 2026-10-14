---
name: generate-changelog
description: Generate a structured CHANGELOG.md (Added/Fixed/Changed/Removed) from git commits since the last tag. Use for /generate-changelog or when asked for release notes.
---

# /generate-changelog

Run `bash skills/generate-changelog/changelog.sh` from the repo root
(add `-v 1.2.0` to name the release, `-o FILE` to change the output).
Then show the user the generated `CHANGELOG.md` and offer to polish wording.

---
name: generate-changelog
description: Generate a deterministic CHANGELOG.md from commits since the latest git tag.
---

# Generate changelog

Run `bash changelog.sh` from the target repository, or pass `--repo PATH` and
`--output PATH`. The generator reads commits since the latest tag, groups them
under Added, Fixed, Changed, and Removed, and writes a valid Markdown file.

Use the exact commit subjects. Conventional prefixes are mapped as follows:
`feat`/`add` → Added, `fix` → Fixed, `remove`/`delete` → Removed, and
`refactor`/`perf`/`docs`/`chore` → Changed. Ambiguous subjects are kept under
Changed; no details are inferred. If there is no tag, all commits are used and
the heading says so. An origin GitHub URL adds commit links.

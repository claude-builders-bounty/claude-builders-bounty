---
name: generate-changelog
description: Generate or update a structured CHANGELOG.md from git history using Conventional Commits. Use when asked to generate a changelog, write release notes, or summarize commits since the last tag.
---

# Generate Changelog

Turn the project's git history into a structured `CHANGELOG.md`. The bundled
script reads all commits since the latest git tag (or full history when no tag
exists), parses [Conventional Commits](https://www.conventionalcommits.org) and
groups them into **Breaking Changes / Added / Fixed / Changed / Removed**:

- `feat:` → Added, `fix:` → Fixed, `refactor:/docs:/chore:/...` → Changed
- descriptions starting with remove/delete/drop → Removed
- `!` or a `BREAKING CHANGE:` footer → Breaking Changes
- non-conventional subjects fall back to Changed (nothing is silently dropped)

## Steps

1. From the repository root run the script that lives next to this file:
   `python <skill-dir>/generate_changelog.py -o CHANGELOG.md`
   (an existing CHANGELOG.md keeps its older sections; the new range is prepended)
2. Read the generated file back and fix any wording that reads poorly —
   commit subjects are raw input, not final prose.
3. Show the user a one-paragraph summary of what landed in each category.

## Options

- `python generate_changelog.py` — print to stdout instead of writing a file
- `--since REF` — override the default range start (latest tag)
- positional repo path — run against another repository

---
name: generate-changelog
description: Generate a structured CHANGELOG.md section from a project's git history since the last tag, auto-categorized into Added / Fixed / Changed / Removed. Use when the user asks to generate or update a changelog, draft release notes, or summarize what changed since the last release.
---

# Generate Changelog

Build a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) style section
from the commits since the last git tag and prepend it to `CHANGELOG.md`.

## Quick start

From the root of any git repository:

```bash
bash changelog.sh
```

Options:

```bash
bash changelog.sh --version 1.2.0          # heading: ## [1.2.0] - <today>
bash changelog.sh --since v0.9.0           # use a specific starting tag
bash changelog.sh --output HISTORY.md      # write to a different file
bash changelog.sh --date 2026-01-31        # override the section date
```

The script prints the generated section to stdout as well, so it can be
pasted straight into a pull request or release notes.

## How commits are categorized

Conventional Commits prefixes are mapped as follows:

| Commit type                                             | Category  |
| ------------------------------------------------------- | --------- |
| `feat:`                                                 | Added     |
| `fix:` (also `bugfix:`, `hotfix:`)                      | Fixed     |
| `perf:`, `refactor:`, `style:`, `docs:`, `chore:`, `build:`, `ci:`, `test:`, `revert:` | Changed |
| `remove:` / `deprecate:`, or a subject starting with remove/delete/drop | Removed |

Additional rules:

- A breaking-change marker (`feat!:`) prefixes the entry with **Breaking:**.
- Non-conventional subjects fall back to keyword detection
  (add/introduce → Added, fix/resolve → Fixed, remove/delete/drop → Removed,
  everything else → Changed).
- Merge commits and changelog-housekeeping commits are skipped.
- If there is no tag yet, the whole history is used. If HEAD is exactly on a
  tag, that tag's release range is used instead of an empty range.

## Doing it without the script

If bash is unavailable, reproduce the same result manually:

1. Find the range: `git describe --tags --abbrev=0` gives the last tag.
2. List subjects: `git log --no-merges --pretty=format:'%s' <tag>..HEAD`
3. Categorize each subject with the table above, strip the `type(scope):`
   prefix, capitalize the first letter, and group under
   `### Added` / `### Fixed` / `### Changed` / `### Removed`
   (only non-empty groups), under a `## [Unreleased] - YYYY-MM-DD` heading.
4. Insert the section into `CHANGELOG.md` above the previous release section.

## Review checklist

- Entries must come from actual commit subjects — never invent changes.
- Keep the commit's own wording; only strip the prefix and capitalize.
- If a category is empty, omit its heading entirely.
- Show the user the generated section before committing it.

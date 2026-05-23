---
name: generate-changelog
description: Generate or refresh a structured CHANGELOG.md from a git repository's commit history. Use when a user asks for a changelog, release notes, commits since the last tag, or categorization into Added, Fixed, Changed, and Removed.
---

# Generate Changelog

Use the bundled `generate_changelog.py` script to create a `CHANGELOG.md` from git history.

## Workflow

1. Confirm the target directory is a git repository.
2. Run `python generate_changelog.py --repo <repo> --dry-run` to preview the changelog.
3. If the preview is correct, run `python generate_changelog.py --repo <repo> --output CHANGELOG.md`.
4. Review the output for duplicates, unclear commit subjects, or release-specific wording before final delivery.

## Categorization Rules

- `Added`: commits beginning with `feat`, `add`, `create`, `introduce`, or containing feature-style additions.
- `Fixed`: commits beginning with `fix`, `bug`, `resolve`, `repair`, or `correct`.
- `Removed`: commits beginning with `remove`, `delete`, `drop`, or `deprecate`.
- `Changed`: dependency bumps, docs, refactors, chores, CI changes, and anything that does not fit the other sections.

Keep commit references short with 7-character SHAs. Preserve input order from oldest to newest so the changelog reads like a release narrative.

## Output Expectations

Generate Markdown with this shape:

```md
# Changelog

## <version> - <date>

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```

Omit empty sections unless the user asks to keep them.

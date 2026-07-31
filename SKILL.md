# Changelog Generator Skill

Generate a structured `CHANGELOG.md` from a project's git history.

## Trigger
`/generate-changelog` or when the user asks to "generate a changelog," "update
changelog," or "create release notes."

## Steps

1. Run `bash changelog.sh` to generate the changelog.
2. Review the output and categorize any commits that were misclassified.
3. Check for duplicate entries and consolidate.
4. Add any additional context (breaking changes, migration notes, security
   fixes) that the commit messages alone don't capture.
5. Present the final `CHANGELOG.md` to the user for review.

## Categorization Rules

| Prefix | Category |
|--------|----------|
| `add`, `feat`, `new`, `create`, `implement`, `introduce` | **Added** |
| `fix`, `bug`, `patch`, `resolve`, `repair`, `hotfix` | **Fixed** |
| `remove`, `drop`, `delete`, `deprecate`, `retire` | **Removed** |
| Everything else | **Changed** |

## Output Format

```markdown
# Changelog

## [version] - YYYY-MM-DD

### Added
- List of new features

### Fixed
- List of bug fixes

### Changed
- List of changes

### Removed
- List of removals
```

## Notes

- The script fetches commits since the last git tag. If no tags exist, it
  uses the first commit in the repository.
- Merge commits are automatically excluded.
- If a category has no entries, `_None_` is used as a placeholder.

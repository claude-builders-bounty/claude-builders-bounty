# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from a repository's git history.

## Setup in 3 steps

1. Copy the `generate-changelog/` folder into the root of a git repository.
2. Run `bash generate-changelog/changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## Options

```bash
bash generate-changelog/changelog.sh --output docs/CHANGELOG.md
bash generate-changelog/changelog.sh --from v1.0.0 --to HEAD
bash generate-changelog/changelog.sh --dry-run
```

## Output format

The script creates:

```markdown
# Changelog

Generated on YYYY-MM-DD from commits since <tag>.

## Unreleased

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```

If no git tag exists, the script uses the repository's full history.


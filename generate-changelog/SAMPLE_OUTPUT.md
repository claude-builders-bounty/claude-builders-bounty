# Sample Output

## Example 1: Basic CHANGELOG

Running `bash scripts/generate-changelog.sh` on this repository:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-12

### Added
- initial README with bounty board
```

## Example 2: With Conventional Commits

```bash
# Create some sample commits
git commit -m "feat: add user authentication"
git commit -m "fix: resolve login timeout issue"
git commit -m "docs: update API documentation"
git commit -m "refactor: optimize database queries"
git commit -m "feat: add dark mode support"
git commit -m "fix: fix memory leak in worker"
git commit -m "chore: update dependencies"

# Tag and generate changelog
git tag -a v1.1.0 -m "Release v1.1.0"
bash scripts/generate-changelog.sh --from-tag v1.0.0 --to-tag v1.1.0
```

Output:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.0] - 2026-04-12

### Added
- add user authentication
- add dark mode support

### Fixed
- resolve login timeout issue
- fix memory leak in worker

### Changed
- update API documentation
- optimize database queries

### Other
- update dependencies
```

## Example 3: Dry Run Mode

```bash
$ bash scripts/generate-changelog.sh --dry-run
Fetching commits from HEAD...
=== Generated CHANGELOG (dry run) ===
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-12

### Added
- new feature description

Summary:
  Added:   1 items
```

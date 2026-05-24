# Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history since the last tag.

## When to use

- Before a release or version bump
- When preparing a PR that documents recent changes
- When the user asks for `/generate-changelog`

## Command

```bash
bash skills/generate-changelog/changelog.sh [OUTPUT_PATH]
```

Default output path: `CHANGELOG.md` in the repository root.

## Behavior

1. Finds the most recent git tag (`git describe --tags --abbrev=0`)
2. Collects commits from that tag to `HEAD` (or all commits if no tag exists)
3. Auto-categorizes commit subjects into:
   - **Added** — feat/add/new/introduce/implement
   - **Fixed** — fix/bugfix/hotfix/patch
   - **Changed** — change/refactor/chore/perf/style/build/ci/test (and uncategorized)
   - **Removed** — remove/delete/drop
4. Writes a dated Markdown changelog section

## Example output

```markdown
# Changelog

## [2026-05-24]

Changes since `v1.0.0`.

### Added

- feat: add user authentication module

### Fixed

- fix: handle null session token on logout

### Changed

- refactor: simplify database connection pool
```

## Notes

- Uses commit **subjects only** (first line of commit message)
- Conventional-commit prefixes improve categorization accuracy
- Safe to run repeatedly; overwrites the output file

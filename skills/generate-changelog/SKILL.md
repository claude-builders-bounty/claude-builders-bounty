---
name: generate-changelog
description: Generates a structured CHANGELOG.md from git history, categorized into Added/Fixed/Changed/Removed since the last git tag. Use when the user asks to generate or update a changelog, release notes, or "changelog dari git".
---

# Generate Changelog

Generate `CHANGELOG.md` from the project's git history, following Keep a Changelog conventions.

## Steps

1. Determine the reference point: the latest git tag (`git describe --tags --abbrev=0`). If the repo has no tags, use the first commit.
2. Collect commits since that reference: `git log --pretty=format:'%h|%s' <ref>..HEAD`.
3. Categorize each commit subject (case-insensitive) into:
   - **Added**: `add`, `new`, `feature`, `feat`, `implement`, `introduce`, `initial`, `create`, `support`
   - **Fixed**: `fix`, `bug`, `resolve`, `patch`, `repair`, `hotfix`, `correct`, `revert`
   - **Removed**: `remove`, `delete`, `drop`, `deprecat`, `cleanup`
   - **Changed**: `change`, `update`, `refactor`, `improve`, `rewrite`, `migrate`, `rename`, `bump`, `upgrade`, `enhance`, `perf`, `docs`, `chore`, `style`, `build`, `ci`, `test`
   - Anything else → **Other**
4. Write `CHANGELOG.md` with this structure:

```markdown
# Changelog

All notable changes to this project are documented in this file.

## [<version-or-ref>] - <YYYY-MM-DD>

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```

## Usage

The project ships a ready-to-run script. From the repo root:

```bash
./changelog.sh          # uses last tag, writes CHANGELOG.md
./changelog.sh v1.2.0   # custom since-ref
```

Always verify the output file was written and show the user a brief summary of counts per category.

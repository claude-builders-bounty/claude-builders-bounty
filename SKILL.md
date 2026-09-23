---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorized into Added / Fixed / Changed / Removed.
---

# /generate-changelog

Generate a `CHANGELOG.md` for the current git repository by reading commits
since the last tag and categorizing each one.

## What it does

1. Finds the most recent git tag (`git describe --tags --abbrev=0`). If no
   tag exists, it uses all commits on HEAD.
2. For each commit, it reads the subject line and categorizes it:
   - **Added** — subjects starting with `feat`, `feature`, `add`, `new`, `support`
   - **Fixed** — `fix`, `bugfix`, `patch`, `hotfix`
   - **Changed** — `change`, `update`, `refactor`, `improve`, `chore`, `perf`, `doc`, `test`, `style` (and any uncategorized commit)
   - **Removed** — `remov*`, `deprecat*`, `delete`, `drop`, `breaking`
3. Strips the conventional-commit prefix so the entry reads naturally
   ("feat: add login" → "Add login").
4. Prepends a new `## <version> (<date>)` section at the top of the existing
   changelog (or creates a fresh one with a `# Changelog` header).

## Usage

```bash
python3 scripts/generate_changelog.py [output_file]
```

- `output_file` is optional; defaults to `CHANGELOG.md` in the current
  directory.
- The repository must have at least one commit and (ideally) at least one
  tag. Without a tag, all history is summarized under today's date.

## Example output

Given commits `feat: add login`, `fix: crash on empty input`, `chore: bump
deps`, `remove legacy api`:

```markdown
# Changelog

## 1.2.0 (2026-09-21)

### Added
- Add login (`a1b2c3d`)

### Fixed
- Crash on empty input (`d4e5f6g`)

### Changed
- Bump deps (`h7i8j9k`)

### Removed
- Legacy api (`m0n1o2p`)
```

## Notes

- Conventional-commit style (`feat:`, `fix:`, etc.) is the most reliable
  trigger for correct categorization. Plain English subjects fall back to
  "Changed".
- The version heading uses the last tag when one exists; otherwise it uses
  today's `YYYY.MM.DD` as a placeholder.

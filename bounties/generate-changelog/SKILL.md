---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history, auto-categorized by commit type."
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
bash changelog.sh [output_file] [--since TAG]
```

- `output_file` - defaults to `CHANGELOG.md`
- `--since TAG` - only include commits after this tag (auto-detects latest tag if omitted)

## How It Works

1. Finds the latest git tag (or uses provided tag)
2. Collects all commits since that tag
3. Categorizes each commit by conventional-commit prefix:
   - `feat:`, `add:`, `new`, `implement` -> **Added**
   - `fix:`, `bug:`, `patch:`, `hotfix` -> **Fixed**
   - `refactor:`, `chore:`, `update:`, `change:`, `improve:`, `bump` -> **Changed**
   - `remove:`, `delete:`, `drop:`, `deprecate` -> **Removed**
   - Everything else -> **Other**
4. Outputs a formatted `CHANGELOG.md`

## Example Output

```markdown
## [Unreleased] - 2026-05-30

### Added
- feat: add user authentication (a1b2c3d)
- new dark mode toggle (e4f5g6h)

### Fixed
- fix: resolve login timeout issue (i7j8k9l)

### Changed
- refactor: simplify database queries (m0n1o2p)
```

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

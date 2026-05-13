# /generate-changelog

Generate a structured CHANGELOG.md from the project's git history.

## Usage

```
/generate-changelog
/generate-changelog --since v1.0.0
/generate-changelog --output HISTORY.md
```

## What it does

1. Finds the last git tag (or uses `--since` tag)
2. Fetches all commits since that tag
3. Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
4. Outputs a formatted `CHANGELOG.md`

## Categorization Rules

| Commit prefix | Category |
|---------------|----------|
| `feat:`, `add:`, `new:` | Added |
| `fix:`, `bug:`, `patch:` | Fixed |
| `refactor:`, `update:`, `change:`, `improve:`, `perf:`, `chore:`, `docs:`, `style:`, `test:`, `ci:`, `build:` | Changed |
| `remove:`, `delete:`, `drop:` | Removed |
| Everything else | Other |

## Implementation

```bash
bash $(dirname "$0")/generate-changelog.sh "$@"
```

## Examples

```bash
# Generate changelog since last tag
bash generate-changelog.sh

# Generate changelog since specific tag
bash generate-changelog.sh --since v2.0.0

# Custom output file
bash generate-changelog.sh --output docs/HISTORY.md
```

## Sample Output

```markdown
# Changelog

## [Unreleased] — 2026-05-14

### Added
- feat: add user authentication (a1b2c3d)
- feat: add dark mode support (e4f5g6h)

### Fixed
- fix: resolve login timeout issue (i7j8k9l)
- fix: correct date format in sidebar (m0n1o2p)

### Changed
- refactor: simplify API routes (q3r4s5t)
- chore: update dependencies (u6v7w8x)
```

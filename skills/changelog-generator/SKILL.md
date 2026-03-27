# Generate CHANGELOG from git history

Generate a structured `CHANGELOG.md` from a project's git commit history, auto-categorized by conventional commit style.

## Usage

```
/generate-changelog
bash changelog.sh
```

The agent runs the script and outputs a `CHANGELOG.md` file in the current directory.

## What it does

1. Finds the last git tag (or starting commit if no tags)
2. Collects all commits since that point
3. Categorizes each commit by prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `perf:` → **Changed** (performance)
   - `refactor:` / `chore:` / `style:` → **Changed**
   - `docs:` → **Changed** (documentation)
   - `test:` → **Changed** (tests)
   - `BREAKING CHANGE:` → **Breaking**
   - `deprecate:` → **Deprecated**
   - `remove:` / `delete:` → **Removed**
4. Outputs a properly formatted `CHANGELOG.md`

## Output format

```markdown
# Changelog

## [Unreleased]

## [1.2.0] - 2026-03-27

### Added
- Feature description from commit message

### Fixed
- Bug fix description

### Changed
- Refactor or improvement

### Removed
- Removed feature
```

## Configuration

Optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CHANGELOG_SINCE` | last tag | Start from specific tag or commit |
| `CHANGELOG_OUTPUT` | CHANGELOG.md | Output filename |
| `CHANGELOG_UNRELEASED` | true | Include unreleased commits |

## Examples

- `bash changelog.sh` — generate full changelog from last tag
- `bash changelog.sh --since v1.0.0` — generate from specific tag
- `bash changelog.sh --output HISTORY.md` — custom output file

## Requirements

- `git`
- `grep`, `sed` (standard unix tools)
- No external dependencies

## Notes

- Commits without recognized prefixes are grouped under **Changed**
- Merge commits are excluded
- commits are sorted newest-first within each category

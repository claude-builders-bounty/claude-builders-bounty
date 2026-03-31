# Generate Changelog

Generate a structured CHANGELOG.md from git history, auto-categorizing commits.

## Usage

```bash
# From project root (after at least one git tag exists)
bash changelog.sh

# Specify a starting tag
bash changelog.sh --since v0.1.0

# Custom output file
bash changelog.sh --output docs/CHANGELOG.md
```

## How it works

1. Finds the last git tag (or uses `--since TAG`)
2. Collects all commits since that tag
3. Categorizes each commit by prefix keyword into **Added / Fixed / Changed / Removed / Other**
4. Outputs a [Keep a Changelog](https://keepachangelog.com/) formatted file

## Commit Prefix Mapping

| Prefix | Category |
|--------|----------|
| `add`, `feat`, `feature`, `new`, `implement`, `create`, `initial`, `introduce` | Added |
| `fix`, `bug`, `patch`, `hotfix`, `resolve`, `repair`, `correct` | Fixed |
| `change`, `update`, `refactor`, `improve`, `upgrade`, `bump`, `modify`, `rename`, `move` | Changed |
| `remove`, `delete`, `deprecate`, `drop`, `revert`, `cleanup`, `clean` | Removed |
| _(anything else)_ | Other |

## Example Output

```markdown
# Changelog

## [v1.0.0] — 2026-04-01

### Added
- Add user authentication module (`abc1234`)
- Implement dark mode toggle (`def5678`)

### Fixed
- Fix login redirect loop (`ghi9012`)

### Changed
- Update dependencies to latest versions (`jkl3456`)
```

## Requirements

- Git repository with commits
- Bash 4+
- A git tag (recommended but not required)

# Changelog Generator Skill

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

```bash
bash changelog.sh                    # Generate from last tag to HEAD
bash changelog.sh --since v1.0.0     # Generate from v1.0.0 to HEAD
bash changelog.sh --output CHANGES.md # Custom output file
bash changelog.sh --repo /path/to/repo # Another repo
bash changelog.sh --help             # Show help
```

## Features

- Zero dependencies beyond `git` and `bash`
- Auto-detects last git tag as starting point
- Parses conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Categorizes into: **Added**, **Fixed**, **Changed**, **Removed**, **Other**
- Silent exit when no new commits exist (idempotent)
- Works on any git repository

## Output Example

```markdown
# Changelog

## [Unreleased] (since v1.0.0)

### Added
- Add user profile page (a1b2c3d)
- Add search functionality (e4f5g6h)

### Fixed
- Fix login redirect loop (i7j8k9l)
```

## Requirements

- Bash 4+
- Git 2.0+
- Linux, macOS, or WSL

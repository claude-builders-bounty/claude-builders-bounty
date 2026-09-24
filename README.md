# Changelog Generator

Generate a structured `CHANGELOG.md` from git commit history.

## Setup (3 steps)

1. **Clone or copy files**: Copy `generate_changelog.py` and `SKILL.md` to your repository root.
2. **Make executable** (optional): `chmod +x generate_changelog.py`
3. **Run**: `python3 generate_changelog.py` or use `/generate-changelog` in Claude Code

## Usage

```bash
# Default output to CHANGELOG.md
python3 generate_changelog.py

# Custom output file
python3 generate_changelog.py my_changelog.md
```

## Features

- Fetches commits since last git tag (or all commits if no tags)
- Auto-categorizes into: Added / Fixed / Changed / Removed / Other
- Outputs properly formatted Markdown
- Includes commit hashes for traceability

## Sample Output

```markdown
# Changelog

## [2026-09-25]

### Added
- c6ea084 implement: complete WP1-WP9 remediation

### Fixed
- 33d69e8 fix: skip catalog-toolkit PDF/DOCX tests

### Changed
- 0a54c51 canonical: update submodule pointers
```

## Tested

Tested on real GitHub repository with 1,739+ commits. See `test_output.md` for sample.

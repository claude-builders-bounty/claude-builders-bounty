# Generate Changelog from Git History

A Python CLI tool that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

1. **Ensure Python 3.7+ and git are installed**
   ```bash
   python --version && git --version
   ```

2. **Run the script inside any git repo**
   ```bash
   python generate_changelog.py
   ```

3. **Done!** `CHANGELOG.md` is created/updated in your project root.

## Usage

```bash
# All commits (auto-prepends to existing CHANGELOG.md)
python generate_changelog.py

# Only commits since last tag (auto-detected)
python generate_changelog.py --since-tag v1.0

# Custom version label and output file
python generate_changelog.py --version v2.0 --output RELEASE_NOTES.md

# Preview without writing
python generate_changelog.py --dry-run

# Point to a different repo
python generate_changelog.py --cwd /path/to/repo
```

## Features

- **Auto-categorizes** commits into `Added`, `Fixed`, `Changed`, `Removed`
- Supports **Conventional Commits** (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to **keyword matching** for non-conventional messages
- **Auto-detects** the last git tag
- **Prepends** to existing CHANGELOG.md (preserves history)
- Includes commit short hash, author, and date
- Zero dependencies (stdlib only)

## Sample Output

```markdown
# Changelog

## [v3.2] - 2026-05-27

### Added
- Add Excel export support with openpyxl ([fd96446](link)) — *Qiu-Difeng*
- Add LICENSE and FUNDING.yml ([755ac79](link)) — *Qiu-Difeng*

### Fixed
- Fix datetime import conflict in github_search.py ([fd96446](link)) — *Qiu-Difeng*

### Changed
- Update README with badges ([755ac79](link)) — *Qiu-Difeng*
- Clean up test files ([755ac79](link)) — *Qiu-Difeng*
```

## Tested On

Tested on [python-mega-scraper-kit](https://github.com/Qiu-Difeng/python-mega-scraper-kit) — a real GitHub repo with 20+ commits and multiple tags.

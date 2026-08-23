# Changelog Generator

Generate a structured `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

1. **Copy the script** to your project:
   ```bash
   cp changelog.sh /path/to/your/project/
   ```

2. **Run it** in your repo:
   ```bash
   cd /path/to/your/project
   bash changelog.sh
   ```

3. **Review** the generated `CHANGELOG.md`:
   ```bash
   cat CHANGELOG.md
   ```

## Usage

```bash
# Use last git tag as starting point
bash changelog.sh

# Specify a starting tag
bash changelog.sh v1.2.0

# Specify a different repo
bash changelog.sh --repo /path/to/repo
```

## Output Format

The generated `CHANGELOG.md` follows the [Keep a Changelog](https://keepachangelog.com/) convention:

```markdown
# Changelog

## [2026-08-24] - 2026-08-24

### Added
- feat: add user authentication (John Doe, 2026-08-20)

### Fixed
- fix: resolve login redirect loop (Jane Smith, 2026-08-21)

### Changed
- refactor: simplify API client (John Doe, 2026-08-22)

### Removed
- remove: drop deprecated v1 endpoints (Jane Smith, 2026-08-23)
```

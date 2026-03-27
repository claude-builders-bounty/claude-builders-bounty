# Generate CHANGELOG from Git History 📋

Bash script that automatically generates a structured `CHANGELOG.md` from your project's git history, following the [Keep a Changelog](https://keepachangelog.com/) format.

## What it does

Reads git commits since the last tag and auto-categorizes them:

| Category | Matched prefixes/keywords |
|----------|--------------------------|
| **Added** | `feat`, `add`, `new`, `create`, `implement` |
| **Fixed** | `fix`, `bug`, `patch`, `resolve`, `hotfix` |
| **Changed** | `refactor`, `chore`, `style`, `perf`, `ci`, `build`, `docs`, `test`, `update` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate` |

## Install (3 steps)

```bash
# 1. Copy the script
cp changelog/changelog.sh ~/.local/bin/changelog.sh
chmod +x ~/.local/bin/changelog.sh

# 2. Navigate to your project
cd /path/to/your/project

# 3. Generate
changelog.sh
# ✅ CHANGELOG written to CHANGELOG.md (42 commits categorized)
```

## Usage

```bash
# Generate CHANGELOG.md (auto-detects version from latest tag)
bash changelog.sh

# Preview without writing file
bash changelog.sh --dry-run

# Specify version label
bash changelog.sh --version "2.0.0"

# Only include commits since a specific tag
bash changelog.sh --since v1.5.0

# Custom output file
bash changelog.sh --output docs/CHANGELOG.md

# Combine options
bash changelog.sh --version "1.3.0" --since v1.2.0 --dry-run
```

## Sample output

```markdown
# Changelog

## [v1.2.0 → HEAD] — 2026-03-28

### Added
- feat: add export to CSV feature (`a1b2c3d`)
- feat(auth): add OAuth2 Google provider (`d4e5f6a`)

### Fixed
- fix: resolve login crash on empty password (`b7c8d9e`)
- fix(ui): button alignment on mobile (`e0f1a2b`)

### Changed
- chore: update dependencies (`c3d4e5f`)
- refactor: extract validation into shared module (`f6a7b8c`)
- docs: update README with API examples (`a9b0c1d`)

### Removed
- remove: drop legacy API v1 endpoints (`d2e3f4a`)
- delete: remove deprecated user.legacy field (`b5c6d7e`)
```

## Testing

```bash
bash changelog/test/test.sh
```

```
📋 CHANGELOG Generator — Test Suite

  ✓ Generates changelog header
  ✓ Has 'Added' section
  ✓ Has 'Fixed' section
  ✓ Has 'Changed' section
  ✓ Has 'Removed' section
  ✓ feat commits categorized as Added
  ✓ fix commits categorized as Fixed
  ✓ delete commits categorized as Removed
  ✓ chore commits categorized as Changed
  ✓ --since tag filters correctly (5 commits since v1.0.0)
  ✓ --version flag sets version label
  ✓ Writes CHANGELOG.md file
  ✓ Includes commit hashes

Results: 13 passed, 0 failed
```

## Requirements

- Bash 4+
- Git

## License

MIT

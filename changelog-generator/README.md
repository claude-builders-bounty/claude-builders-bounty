# Changelog Generator

> Generate structured CHANGELOGs from git history with automatic semantic categorization.

## Quick Start

### Option 1: Bash (Zero Dependencies)

```bash
chmod +x changelog.sh
./changelog.sh
```

### Option 2: Python (Richer Output)

```bash
chmod +x changelog.py
python3 changelog.py
```

### Option 3: Custom Range

```bash
./changelog.sh CHANGELOG.md v1.0.0
# or
python3 changelog.py v1.0.0 CHANGELOG.md
```

## What You Get

```markdown
# CHANGELOG

## [Unreleased] - 2026-03-29

### Added
- feat: add user authentication

### Changed
- refactor: update API client

### Fixed
- fix: resolve login timeout

### Security
(none)

### Performance
- perf: optimize database queries
```

## How It Works

Both scripts:
1. Fetch commits since the last git tag
2. Categorize by keywords (feat, fix, perf, etc.)
3. Output structured markdown
4. Deduplicate entries

**Categories:**
- **Added** — feat, add, new
- **Fixed** — fix, bug, patch
- **Changed** — change, update, refactor
- **Removed** — remove, delete, deprecate
- **Security** — security, vuln, cve
- **Performance** — perf, optimize, speed

## Requirements

- Git 2.0+
- Bash 4.0+ (for bash version)
- Python 3.6+ (for Python version)

## Real Example

Tested on this repository:

```bash
cd /tmp/test-repo
python3 ../changelog-generator/changelog.py
```

Output:
```
📝 Fetching commits since HEAD~20...
✅ CHANGELOG generated: CHANGELOG.md

📊 Summary:
   Total commits: 3
   Added: 1
   Changed: 1
   Fixed: 1
```

## License

MIT

# CHANGELOG Generator

A Python tool that automatically generates a structured `CHANGELOG.md` from your project's git history.

## Features

- Auto-detects the last git tag and fetches commits since then
- Categorizes commits into: **Added** / **Fixed** / **Changed** / **Removed**
- Smart pattern matching on conventional commit prefixes
- Filters out merge commits and automated bump messages
- Prepends new entries to an existing CHANGELOG.md
- Zero external dependencies -- Python 3 stdlib only

## Setup

1. Download `changelog.py` to your project root
2. Run it:

```bash
python3 changelog.py
```

## Usage

```bash
# Generate from last tag to HEAD (default)
python3 changelog.py

# Generate from a specific tag
python3 changelog.py --tag v1.0.0

# Custom output file
python3 changelog.py --output docs/CHANGELOG.md

# Specify repository path
python3 changelog.py --repo /path/to/repo
```

## Output Example

```markdown
## [v1.0.0] - 2026-05-31

### Added
- Add user authentication module (a1b2c3d4)
- Implement dark mode toggle (e5f6g7h8)

### Fixed
- Fix login redirect loop (i9j0k1l2)

### Changed
- Update API endpoint to v2 (m3n4o5p6)

### Removed
- Remove deprecated legacy parser (q7r8s9t0)
```

## How It Works

1. Reads git log from the last tag (or all history if no tags exist)
2. Parses each commit subject line against categorized patterns
3. Groups commits by category (Added, Fixed, Changed, Removed)
4. Formats output and writes/updates `CHANGELOG.md`
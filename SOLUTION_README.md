# Changelog Generator

Generate structured `CHANGELOG.md` from git history.

## Setup (3 steps)

```bash
# 1. Clone this repo or copy changelog.py into your project
curl -O https://raw.githubusercontent.com/MageAlex/claude-builders-bounty/main/changelog.py

# 2. Make it executable
chmod +x changelog.py

# 3. Tag a release
git tag v1.0.0
```

## Usage

```bash
# Between two most recent tags
python3 changelog.py

# With version prefix
python3 changelog.py --tag-prefix v

# Append to existing CHANGELOG
python3 changelog.py --append
```

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2026-06-15

### Added
- Introduce dark mode support (a1b2c3d)

### Fixed
- Fix login redirect on timeout (e4f5g6h)

### Changed
- Refactor auth middleware (i7j8k9l)

### Removed
- Drop deprecated legacy API (m0n1o2p)
```

## Sample

Tested on [this repo](https://github.com/claude-builders-bounty/claude-builders-bounty):

```bash
git tag v0.1.0 HEAD~3
git tag v0.2.0 HEAD
python3 changelog.py --tag-prefix v
```

Produces a categorized changelog with commits sorted into Added/Fixed/Changed/Removed.

## Requirements

- Python 3.8+
- Git
